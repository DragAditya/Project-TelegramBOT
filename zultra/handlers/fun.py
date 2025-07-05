"""
Fun command handlers for Zultra Telegram Bot.
Handles entertainment commands like truth, dare, games, etc.
"""

import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger

from ..db.database import get_session, create_or_update_user


class FunHandlers:
    """Fun and entertainment command handlers."""
    
    def __init__(self):
        self.truth_questions = [
            "What's the most embarrassing thing you've ever done?",
            "What's your biggest fear?",
            "Who was your first crush?",
            "What's the weirdest dream you've ever had?",
            "What's your most embarrassing childhood memory?",
            "What's the most childish thing you still do?",
            "What's your worst habit?",
            "What's the biggest lie you've ever told?",
            "What's something you've never told anyone?",
            "What's your biggest regret?",
            "What's the most trouble you've ever been in?",
            "What's your guilty pleasure?",
            "What's the strangest thing you've eaten?",
            "What's your most irrational fear?",
            "What's the worst advice you've ever given?",
            "What's your most embarrassing autocorrect fail?",
            "What's the weirdest thing you've googled?",
            "What's your strangest habit?",
            "What's the most awkward situation you've been in?",
            "What's something you pretend to understand but don't?"
        ]
        
        self.dare_challenges = [
            "Sing your favorite song out loud",
            "Do 10 push-ups",
            "Call a random contact and say 'I love you'",
            "Post an embarrassing photo on social media",
            "Dance for 30 seconds without music",
            "Speak in an accent for the next 10 minutes",
            "Do your best impression of a celebrity",
            "Send a funny selfie to the group",
            "Write a poem about pizza",
            "Do the chicken dance",
            "Speak only in questions for 5 minutes",
            "Do your best animal impression",
            "Sing the alphabet backwards",
            "Do a cartwheel (or attempt one)",
            "Act like your favorite movie character",
            "Do 20 jumping jacks",
            "Speak in rhymes for 3 minutes",
            "Do your best robot dance",
            "Pretend to be a news anchor",
            "Do your favorite TikTok dance"
        ]
        
        self.eightball_responses = [
            "🎱 It is certain",
            "🎱 It is decidedly so",
            "🎱 Without a doubt",
            "🎱 Yes definitely",
            "🎱 You may rely on it",
            "🎱 As I see it, yes",
            "🎱 Most likely",
            "🎱 Outlook good",
            "🎱 Yes",
            "🎱 Signs point to yes",
            "🎱 Reply hazy, try again",
            "🎱 Ask again later",
            "🎱 Better not tell you now",
            "🎱 Cannot predict now",
            "🎱 Concentrate and ask again",
            "🎱 Don't count on it",
            "🎱 My reply is no",
            "🎱 My sources say no",
            "🎱 Outlook not so good",
            "🎱 Very doubtful"
        ]
        
        self.quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "The only impossible journey is the one you never begin. - Tony Robbins",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
            "The way to get started is to quit talking and begin doing. - Walt Disney",
            "Don't let yesterday take up too much of today. - Will Rogers",
            "You learn more from failure than from success. Don't let it stop you. - Unknown",
            "If you are working on something that you really care about, you don't have to be pushed. - Steve Jobs",
            "Experience is a hard teacher because she gives the test first, the lesson afterward. - Vernon Law",
            "Don't be afraid to give up the good to go for the great. - John D. Rockefeller",
            "Don't let what you cannot do interfere with what you can do. - John Wooden",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "The only person you are destined to become is the person you decide to be. - Ralph Waldo Emerson"
        ]
        
        self.roasts = [
            "You're like a software update - whenever I see you, I think 'not now'",
            "If I had a dollar for every brain cell you have, I'd have 25 cents",
            "You're proof that evolution can go in reverse",
            "I'd explain it to you, but I don't have any crayons with me",
            "You're like a participation trophy - everyone gets one, but nobody really wants it",
            "If stupidity was a superpower, you'd be unstoppable",
            "You're the reason they put instructions on shampoo bottles",
            "I'm not saying you're dumb, but you make me miss my ex",
            "You're like a broken pencil - completely pointless",
            "If brains were dynamite, you wouldn't have enough to blow your nose"
        ]
        
        self.ship_emojis = ["💕", "💖", "💗", "💘", "💝", "💞", "💟", "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"]
    
    async def truth_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /truth command with random truth questions."""
        try:
            user = update.effective_user
            question = random.choice(self.truth_questions)
            
            truth_text = f"""
🤔 <b>Truth Time!</b>

<b>Question for {user.first_name}:</b>
{question}

<i>Answer honestly! 😏</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Truth", callback_data="new_truth"),
                    InlineKeyboardButton("😈 Dare Instead", callback_data="new_dare")
                ],
                [
                    InlineKeyboardButton("🎮 More Games", callback_data="fun_menu")
                ]
            ])
            
            await update.message.reply_text(
                truth_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Truth command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in truth command: {e}")
            await update.message.reply_text("❌ Error getting truth question. Try again!")
    
    async def dare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /dare command with random dare challenges."""
        try:
            user = update.effective_user
            challenge = random.choice(self.dare_challenges)
            
            dare_text = f"""
😈 <b>Dare Challenge!</b>

<b>Challenge for {user.first_name}:</b>
{challenge}

<i>Are you brave enough? 💪</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Dare", callback_data="new_dare"),
                    InlineKeyboardButton("🤔 Truth Instead", callback_data="new_truth")
                ],
                [
                    InlineKeyboardButton("✅ Completed!", callback_data="dare_completed"),
                    InlineKeyboardButton("😅 Skip This One", callback_data="new_dare")
                ]
            ])
            
            await update.message.reply_text(
                dare_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Dare command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in dare command: {e}")
            await update.message.reply_text("❌ Error getting dare challenge. Try again!")
    
    async def eightball_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /8ball command with magic 8-ball responses."""
        try:
            user = update.effective_user
            question = ' '.join(context.args) if context.args else None
            
            if not question:
                await update.message.reply_text(
                    "🎱 <b>Magic 8-Ball</b>\n\n"
                    "Ask me a yes/no question!\n"
                    "<i>Usage: /8ball Will I be successful?</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Add some suspense
            thinking_msg = await update.message.reply_text("🎱 <i>Shaking the magic 8-ball...</i>", parse_mode=ParseMode.HTML)
            await asyncio.sleep(2)
            
            response = random.choice(self.eightball_responses)
            
            result_text = f"""
🎱 <b>Magic 8-Ball</b>

<b>Question:</b> {question}

<b>Answer:</b> {response}

<i>The magic 8-ball has spoken! ✨</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Ask Again", callback_data="eightball_again"),
                    InlineKeyboardButton("🎮 More Games", callback_data="fun_menu")
                ]
            ])
            
            await thinking_msg.edit_text(
                result_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"8ball command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in 8ball command: {e}")
            await update.message.reply_text("❌ Error with magic 8-ball. Try again!")
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /quote command with inspirational quotes."""
        try:
            quote = random.choice(self.quotes)
            
            quote_text = f"""
💫 <b>Inspirational Quote</b>

<i>"{quote}"</i>

<b>✨ Let this inspire your day! ✨</b>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Quote", callback_data="new_quote"),
                    InlineKeyboardButton("📤 Share", callback_data="share_quote")
                ],
                [
                    InlineKeyboardButton("💾 Save Quote", callback_data="save_quote"),
                    InlineKeyboardButton("🎮 More Fun", callback_data="fun_menu")
                ]
            ])
            
            await update.message.reply_text(
                quote_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Quote command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in quote command: {e}")
            await update.message.reply_text("❌ Error getting quote. Try again!")
    
    async def roast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /roast command with funny roasts."""
        try:
            user = update.effective_user
            target = None
            
            # Check if roasting someone specific
            if context.args:
                target_text = ' '.join(context.args)
                if target_text.startswith('@'):
                    target = target_text
                else:
                    target = target_text
            
            roast = random.choice(self.roasts)
            
            if target:
                roast_text = f"""
🔥 <b>Roast Time!</b>

<b>Target:</b> {target}
<b>Roast:</b> {roast}

<i>It's all in good fun! 😄</i>
"""
            else:
                roast_text = f"""
🔥 <b>Random Roast</b>

{roast}

<i>Don't take it personally! 😜</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Roast", callback_data="new_roast"),
                    InlineKeyboardButton("😂 Counter Roast", callback_data="counter_roast")
                ],
                [
                    InlineKeyboardButton("🎮 More Games", callback_data="fun_menu")
                ]
            ])
            
            await update.message.reply_text(
                roast_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Roast command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in roast command: {e}")
            await update.message.reply_text("❌ Error generating roast. Try again!")
    
    async def ship_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ship command for compatibility matching."""
        try:
            user = update.effective_user
            
            if len(context.args) < 2:
                await update.message.reply_text(
                    "💕 <b>Ship Compatibility</b>\n\n"
                    "Ship two people together!\n"
                    "<i>Usage: /ship @user1 @user2</i>\n"
                    "<i>Or: /ship Alice Bob</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            person1 = context.args[0]
            person2 = context.args[1]
            
            # Generate compatibility percentage
            compatibility = random.randint(1, 100)
            
            # Generate ship name
            if person1.startswith('@'):
                name1 = person1[1:]
            else:
                name1 = person1
            
            if person2.startswith('@'):
                name2 = person2[1:]
            else:
                name2 = person2
            
            ship_name = name1[:len(name1)//2] + name2[len(name2)//2:]
            
            # Get compatibility description
            if compatibility >= 90:
                description = "Perfect match! 💍"
                emoji = "💖"
            elif compatibility >= 70:
                description = "Great chemistry! 💕"
                emoji = "💗"
            elif compatibility >= 50:
                description = "Good potential! 💘"
                emoji = "💛"
            elif compatibility >= 30:
                description = "Might work with effort! 💙"
                emoji = "💙"
            else:
                description = "Better as friends! 💙"
                emoji = "💔"
            
            # Generate compatibility bar
            filled_hearts = compatibility // 10
            empty_hearts = 10 - filled_hearts
            bar = "💖" * filled_hearts + "🤍" * empty_hearts
            
            ship_text = f"""
💕 <b>Ship Compatibility</b>

<b>{person1} + {person2}</b>
<b>Ship Name:</b> {ship_name}

<b>Compatibility:</b> {compatibility}%
{bar}

<b>Status:</b> {description} {emoji}

<i>Results are for entertainment only! 😄</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Ship Again", callback_data="ship_again"),
                    InlineKeyboardButton("📤 Share Result", callback_data="share_ship")
                ],
                [
                    InlineKeyboardButton("💕 Ship Me", callback_data="ship_me"),
                    InlineKeyboardButton("🎮 More Games", callback_data="fun_menu")
                ]
            ])
            
            await update.message.reply_text(
                ship_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Ship command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in ship command: {e}")
            await update.message.reply_text("❌ Error creating ship. Try again!")
    
    async def game_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /game command with interactive games menu."""
        try:
            game_text = """
🎮 <b>Interactive Games Menu</b>

Choose a game to play:

🎯 <b>Quick Games:</b>
• Number Guessing Game
• Rock Paper Scissors
• Word Association
• Riddle Challenge

🎲 <b>Random Fun:</b>
• Truth or Dare
• Magic 8-Ball
• Compatibility Test
• Random Facts

🏆 <b>Challenges:</b>
• Daily Challenge
• Group Challenges
• Trivia Quiz
• Memory Game

<i>Select a game below to start playing! 🎉</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔢 Number Game", callback_data="game_number"),
                    InlineKeyboardButton("✂️ Rock Paper Scissors", callback_data="game_rps")
                ],
                [
                    InlineKeyboardButton("🧩 Riddle", callback_data="game_riddle"),
                    InlineKeyboardButton("🧠 Trivia", callback_data="game_trivia")
                ],
                [
                    InlineKeyboardButton("🎯 Random Game", callback_data="game_random"),
                    InlineKeyboardButton("🏆 Daily Challenge", callback_data="game_daily")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Fun Menu", callback_data="fun_menu")
                ]
            ])
            
            await update.message.reply_text(
                game_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Game command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in game command: {e}")
            await update.message.reply_text("❌ Error loading games menu. Try again!")
    
    async def meme_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /meme command with meme generation."""
        try:
            memes = [
                "🐕 This is fine... everything is fine 🔥",
                "🤔 Big brain time! 🧠",
                "📈 Stonks! 💎",
                "😎 Always has been 🔫",
                "🦆 Peace was never an option",
                "🐸 It is Wednesday my dudes",
                "🎭 Surprised Pikachu face!",
                "🤡 We live in a society",
                "💪 Return to monke",
                "🚀 To the moon! 🌙"
            ]
            
            meme = random.choice(memes)
            
            meme_text = f"""
😂 <b>Random Meme</b>

{meme}

<i>Hope this made you smile! 😄</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Meme", callback_data="new_meme"),
                    InlineKeyboardButton("📤 Share", callback_data="share_meme")
                ]
            ])
            
            await update.message.reply_text(
                meme_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Meme command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in meme command: {e}")
            await update.message.reply_text("❌ Error generating meme. Try again!")
    
    async def joke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /joke command with random jokes."""
        try:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a fake noodle? An impasta!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
                "Why don't skeletons fight each other? They don't have the guts.",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why was the math book sad? Because it had too many problems.",
                "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!"
            ]
            
            joke = random.choice(jokes)
            
            joke_text = f"""
😂 <b>Random Joke</b>

{joke}

<i>Ba dum tss! 🥁</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Another Joke", callback_data="new_joke"),
                    InlineKeyboardButton("📤 Share", callback_data="share_joke")
                ]
            ])
            
            await update.message.reply_text(
                joke_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Joke command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in joke command: {e}")
            await update.message.reply_text("❌ Error getting joke. Try again!")
    
    async def fact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /fact command with random interesting facts."""
        try:
            facts = [
                "🐙 Octopuses have three hearts and blue blood!",
                "🦒 A giraffe's tongue is 18-20 inches long!",
                "🍯 Honey never spoils - it's been found in ancient Egyptian tombs!",
                "🐧 Penguins can't taste sweet, sour, or spicy foods!",
                "🌙 The Moon is moving away from Earth at 3.8 cm per year!",
                "🐨 Koalas sleep 18-22 hours per day!",
                "🦈 Sharks have been around longer than trees!",
                "🐛 Butterflies taste with their feet!",
                "🌍 A day on Venus is longer than its year!",
                "🐘 Elephants are afraid of bees!"
            ]
            
            fact = random.choice(facts)
            
            fact_text = f"""
🤓 <b>Random Fact</b>

{fact}

<i>The more you know! ⭐</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Fact", callback_data="new_fact"),
                    InlineKeyboardButton("📤 Share", callback_data="share_fact")
                ]
            ])
            
            await update.message.reply_text(
                fact_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Fact command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in fact command: {e}")
            await update.message.reply_text("❌ Error getting fact. Try again!")
    
    async def dice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /dice command with dice rolling."""
        try:
            # Determine number of dice and sides
            num_dice = 1
            sides = 6
            
            if context.args:
                try:
                    if 'd' in context.args[0]:
                        # Format: 2d6 or 1d20
                        parts = context.args[0].lower().split('d')
                        num_dice = int(parts[0]) if parts[0] else 1
                        sides = int(parts[1])
                    else:
                        # Just number of sides
                        sides = int(context.args[0])
                except ValueError:
                    await update.message.reply_text(
                        "🎲 <b>Invalid format!</b>\n\n"
                        "Use: /dice or /dice 20 or /dice 2d6",
                        parse_mode=ParseMode.HTML
                    )
                    return
            
            # Limit dice and sides
            num_dice = min(max(num_dice, 1), 10)
            sides = min(max(sides, 2), 100)
            
            # Roll dice
            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            total = sum(rolls)
            
            dice_text = f"""
🎲 <b>Dice Roll Results</b>

<b>Dice:</b> {num_dice}d{sides}
<b>Rolls:</b> {' + '.join(map(str, rolls))}
<b>Total:</b> {total}

<i>Good luck! 🍀</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Roll Again", callback_data="roll_again"),
                    InlineKeyboardButton("🎲 Custom Dice", callback_data="custom_dice")
                ]
            ])
            
            await update.message.reply_text(
                dice_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Dice command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in dice command: {e}")
            await update.message.reply_text("❌ Error rolling dice. Try again!")
    
    async def flip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /flip command for coin flipping."""
        try:
            # Add suspense
            flipping_msg = await update.message.reply_text("🪙 <i>Flipping coin...</i>", parse_mode=ParseMode.HTML)
            await asyncio.sleep(1.5)
            
            result = random.choice(["Heads", "Tails"])
            emoji = "👑" if result == "Heads" else "🦅"
            
            flip_text = f"""
🪙 <b>Coin Flip Result</b>

{emoji} <b>{result}!</b>

<i>The coin has decided! ✨</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Flip Again", callback_data="flip_again"),
                    InlineKeyboardButton("🎮 More Games", callback_data="fun_menu")
                ]
            ])
            
            await flipping_msg.edit_text(
                flip_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Flip command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in flip command: {e}")
            await update.message.reply_text("❌ Error flipping coin. Try again!")