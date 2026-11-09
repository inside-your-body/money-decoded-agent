"""Channel branding pictures for the Persian channel (owner Nov 9): ChatGPT (OpenAI image API) draws profile-picture and banner
artwork WITHOUT any text (image models misspell Persian); the Persian name is typeset afterwards with the owner's fonts.
Output -> samples/brand/."""
import pathlib
from .common import ROOT
from . import images

NO_TEXT = (" Absolutely NO text, letters, numbers, logos or watermarks anywhere in the image (also not on coins, screens or papers).")
PROFILE = {
    'p1_coin_bubble': "Premium app-icon style 3D illustration, centered on a vibrant orange-to-amber gradient background: a glossy golden coin "
                      "bursting out of a friendly white speech bubble, small sparkles, soft studio lighting, clean modern, high contrast, round composition.",
    'p2_rocket_chart': "Premium app-icon style 3D illustration on a deep navy background with a warm orange glow: a stack of shiny gold coins with a "
                       "bold rising green market arrow curving upward behind them, glossy, clean modern, centered, round composition.",
    'p3_lightbulb': "Premium app-icon style 3D illustration on a vibrant orange background: a glowing light bulb whose filament is a golden coin, "
                    "small floating coins around it, idea + money, glossy, soft shadows, clean modern, centered, round composition.",
    'p4_piggy_glasses': "Premium app-icon style 3D illustration on a teal-to-navy gradient background: a cute smart piggy bank wearing round glasses "
                        "with a gold coin entering its slot, friendly, glossy, clean modern, centered, round composition.",
}
BANNER = {
    'b1_finance_glow': "Ultra-wide YouTube channel banner artwork, premium finance theme: deep navy background with soft orange and teal glows, a glowing "
                       "rising market line and faint candlestick chart, glossy gold coins floating on the far left and far right edges, subtle grid, "
                       "cinematic depth. The CENTER of the image (the middle 60% width, middle 40% height) is calm and EMPTY dark space for text.",
    'b2_city_money': "Ultra-wide YouTube channel banner artwork: a stylized modern city skyline at dusk in navy and warm orange tones, glowing financial "
                     "charts in the sky, golden coins and banknotes floating near the left and right edges, premium 3D illustration style. The CENTER "
                     "of the image (middle 60% width, middle 40% height) is calm and EMPTY for text.",
    'b3_flat_bold': "Ultra-wide YouTube channel banner artwork in bold modern flat 3D style: orange background with navy and yellow shapes, coins, a piggy "
                    "bank, a bar chart and an upward arrow arranged ONLY along the far left and far right edges; the whole CENTER is a clean empty "
                    "orange area for text. Playful but premium, high contrast.",
}


def main():
    out = ROOT / 'samples/brand'; out.mkdir(parents=True, exist_ok=True)
    for k, p in PROFILE.items():
        print(k, images.gen(p + NO_TEXT, out / f'{k}.png', size='1024x1024', quality='high'))
    for k, p in BANNER.items():
        print(k, images.gen(p + NO_TEXT, out / f'{k}.png', size='1536x1024', quality='high'))


if __name__ == '__main__':
    main()
