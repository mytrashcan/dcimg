import asyncio
from Module.dcbot import DCBot
from Module.config import TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, get_discord_intents

CHANNEL_IDS = ['1352993534747086949', '1337336259605037096']  # 여러 채널 ID를 리스트로 설정
BASE_URL = "https://gall.dcinside.com/mgallery/board/lists?id=bang_dream"

async def main():
    intents = get_discord_intents()
    bot = DCBot(
        token=TOKEN,
        base_url=BASE_URL,
        channel_ids=CHANNEL_IDS,
        telegram_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        intents=intents,
    )
    await bot.run_bot()

if __name__ == "__main__":
    asyncio.run(main())