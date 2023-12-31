#!/usr/bin/env python3

import asyncio
from nio import AsyncClient, UploadResponse
import requests
from lxml import html
from datetime import datetime as dt
import configparser
import sys
import os
from PIL import Image


def downloadImage(url):
    image = requests.get(url)
    if image.status_code != 200:
        print("error getting image", file=sys.stderr)
        return

    f = open("image", "w+b")
    f.write(image.content)
    f.close()


async def main():
    dirpath = os.path.dirname(os.path.abspath(__file__))
    configParser = configparser.RawConfigParser()
    configFilePath = dirpath + "/config.ini"

    configParser.read(configFilePath)

    HSURL = configParser.get("matrix", "HSURL")
    UserID = configParser.get("matrix", "UserID")
    PW = configParser.get("matrix", "PW")
    minutes = int(configParser.get("matrix", "updateInterval"))

    client = AsyncClient(HSURL, UserID)
    await client.login(PW)

    with open(dirpath + "/channels.csv") as f:
        channelsText = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    channelsText = [x.strip() for x in channelsText]

    now = dt.utcnow()

    for channel in channelsText:
        tgChannel, matrixChannel = channel.split(";")
        page = requests.get("https://t.me/s/" + tgChannel)

        if page.status_code != 200:
            print("error getting channel page", file=sys.stderr)
            sys.exit(1)

        tree = html.fromstring(page.content)
        posted = False

        for s in tree.cssselect(".tgme_widget_message_wrap"):
            postedDate = dt.strptime(
                s.cssselect("time")[-1].get("datetime"), "%Y-%m-%dT%H:%M:%S+00:00"
            )

            if (now - postedDate).total_seconds() < 60 * minutes:
                posted = True

                origLink = s.cssselect(".tgme_widget_message_date")[0].get("href")
                textElement = s.cssselect(".tgme_widget_message_text.js-message_text")
                if len(textElement) == 0:
                    # consider a non-supported message
                    # just send a link
                    text = "This post is only available in telegram (content type not supported).\n"
                    text += "See " + origLink

                    sendResult = await client.room_send(
                        room_id=matrixChannel,
                        message_type="m.room.message",
                        content={
                            "msgtype": "m.text",
                            "body": text,
                        },
                    )

                    continue

                textElement = textElement[0]
                htmlMessage = html.tostring(textElement).decode("utf-8")

                image = s.cssselect(".tgme_widget_message_photo_wrap")

                if len(image) > 0:
                    imageSrc = image[0].get("style").split("'")[1]
                    downloadImage(imageSrc)

                    with open("image", "r+b") as f:
                        matrixPath, _ = await client.upload(
                            f, content_type="image/jpeg"
                        )

                    with Image.open("image") as f:
                        w, h = f.size

                    if not isinstance(matrixPath, UploadResponse):
                        print(
                            f"Failed to upload image. Failure response: {matrixPath}",
                            file=sys.stderr,
                        )

                    await client.room_send(
                        room_id=matrixChannel,
                        message_type="m.room.message",
                        content={
                            "body": "some image",
                            "info": {
                                "mimetype": "image/jpeg",
                                "thumbnail_info": None,
                                "thumbnail_url": matrixPath.content_uri,
                                "w": w / h * 300,
                                "h": 300,
                            },
                            "msgtype": "m.image",
                            "url": matrixPath.content_uri,
                        },
                    )

                print(htmlMessage)
                await client.room_send(
                    room_id=matrixChannel,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "format": "org.matrix.custom.html",
                        "body": textElement.text_content(),
                        "formatted_body": "<div>Original post: {}</div>{}".format(
                            origLink, htmlMessage
                        ),
                    },
                )
        if not posted:
            print("nothing to post for " + tgChannel)
    await client.logout()
    await client.close()


asyncio.get_event_loop().run_until_complete(main())

