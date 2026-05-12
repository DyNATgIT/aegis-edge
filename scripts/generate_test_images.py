from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random
import math

OUTPUT_DIR = Path(".") / "data" / "test_images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMG_WIDTH  = 1200
IMG_HEIGHT = 900


def add_image_label(img: Image.Image, label: str) -> Image.Image:
    """Add a small label to the image for identification."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 300, 28], fill=(0, 0, 0, 180))
    draw.text((5, 5), label, fill=(255, 255, 255))
    return img


def noise_pixels(img: Image.Image, intensity: float = 0.05) -> Image.Image:
    """Add subtle noise to make image look more realistic."""
    import numpy as np
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity * 255, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


# ── IMAGE 1: Partial Thickness Burn — Forearm ────────────
def generate_burn_partial():
    """
    Partial thickness burn on forearm.
    Characteristics: red/pink moist appearance, blistering zones,
    clear wound margins, surrounding erythema.
    Model should identify: partial thickness, 8-12% TBSA, IMMEDIATE risk.
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (205, 155, 120))
    draw = ImageDraw.Draw(img)

    # Normal skin background with texture
    for _ in range(800):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        r = random.randint(1, 4)
        variation = random.randint(-15, 15)
        base = (205 + variation, 155 + variation, 120 + variation)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=base)

    # Main burn area — red/pink moist zone
    burn_x, burn_y = 300, 200
    burn_w, burn_h = 650, 520

    # Outer erythema ring (redness surrounding burn)
    draw.ellipse(
        [burn_x - 40, burn_y - 40, burn_x + burn_w + 40, burn_y + burn_h + 40],
        fill=(220, 80, 70)
    )

    # Main burn bed — moist pink/red
    for i in range(15):
        offset = i * 4
        r_val = max(180, 240 - i * 4)
        g_val = max(60,  100 - i * 3)
        b_val = max(60,   80 - i * 2)
        draw.ellipse(
            [burn_x + offset, burn_y + offset,
             burn_x + burn_w - offset, burn_y + burn_h - offset],
            fill=(r_val, g_val, b_val)
        )

    # Blistering zones — fluid-filled raised areas
    blister_positions = [
        (420, 310, 90, 60),
        (560, 420, 70, 50),
        (680, 280, 110, 75),
        (490, 550, 80, 55),
        (750, 450, 65, 45),
        (380, 480, 55, 40),
    ]
    for bx, by, bw, bh in blister_positions:
        # Blister base — yellowish fluid
        draw.ellipse([bx, by, bx+bw, by+bh], fill=(255, 220, 150))
        # Blister highlight — shiny/fluid appearance
        draw.ellipse(
            [bx + bw//4, by + bh//4,
             bx + bw*3//4, by + bh*3//4],
            fill=(255, 245, 200)
        )
        # Blister rim
        draw.ellipse([bx, by, bx+bw, by+bh], outline=(200, 150, 100), width=2)

    # Deep zone — darker, possibly full-thickness area
    draw.ellipse([550, 350, 750, 520], fill=(160, 80, 60))
    draw.ellipse([580, 370, 720, 500], fill=(140, 65, 50))

    # Wound margin — clear demarcation
    draw.ellipse(
        [burn_x, burn_y, burn_x + burn_w, burn_y + burn_h],
        outline=(180, 60, 50), width=3
    )

    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = noise_pixels(img, 0.03)
    img = add_image_label(img, "BURN - PARTIAL THICKNESS - LEFT FOREARM")

    path = str(OUTPUT_DIR / "burn_partial.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── IMAGE 2: Full Thickness Burn ─────────────────────────
def generate_burn_full_thickness():
    """
    Full thickness burn.
    Characteristics: white/brown/charred, leathery appearance,
    clearly necrotic tissue, distinct from surrounding skin.
    Model should identify: full thickness, no pain (nerve destruction).
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (200, 150, 115))
    draw = ImageDraw.Draw(img)

    # Normal skin surrounding
    for _ in range(600):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        r = random.randint(1, 5)
        v = random.randint(-20, 20)
        draw.ellipse([x-r, y-r, x+r, y+r],
                     fill=(200+v, 150+v//2, 115+v//3))

    # Eschar — full thickness — white/brown/charred
    draw.ellipse([250, 180, 950, 720], fill=(160, 120, 80))
    draw.ellipse([270, 200, 930, 700], fill=(180, 145, 95))

    # Charred central zones
    char_zones = [
        (350, 280, 200, 150, (60, 40, 30)),
        (600, 350, 180, 130, (50, 35, 25)),
        (480, 500, 160, 120, (70, 50, 35)),
        (720, 420, 140, 100, (55, 38, 28)),
    ]
    for cx, cy, cw, ch, color in char_zones:
        draw.ellipse([cx, cy, cx+cw, cy+ch], fill=color)
        # Texture within char zone
        for _ in range(30):
            tx = random.randint(cx, cx+cw)
            ty = random.randint(cy, cy+ch)
            tv = random.randint(-10, 10)
            draw.ellipse(
                [tx-3, ty-3, tx+3, ty+3],
                fill=(color[0]+tv, color[1]+tv, color[2]+tv)
            )

    # Leathery texture — white/pale areas
    white_zones = [
        (420, 310, 150, 100),
        (650, 260, 130, 90),
        (500, 480, 170, 110),
        (730, 500, 120, 85),
    ]
    for wx, wy, ww, wh in white_zones:
        draw.ellipse([wx, wy, wx+ww, wy+wh], fill=(210, 195, 175))

    # Wound margins
    draw.ellipse([250, 180, 950, 720], outline=(100, 70, 50), width=4)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img = noise_pixels(img, 0.025)
    img = add_image_label(img, "BURN - FULL THICKNESS - FOREARM/CHEST")

    path = str(OUTPUT_DIR / "burn_full_thickness.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── IMAGE 3: Deep Laceration ─────────────────────────────
def generate_laceration_deep():
    """
    Deep laceration — potential tendon/vessel involvement.
    Characteristics: linear wound with ragged edges, exposed deeper
    tissue, surrounding bruising.
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (198, 148, 112))
    draw = ImageDraw.Draw(img)

    # Skin background
    for _ in range(700):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        r = random.randint(1, 5)
        v = random.randint(-18, 18)
        draw.ellipse([x-r, y-r, x+r, y+r],
                     fill=(198+v, 148+v//2, 112+v//3))

    # Surrounding bruising / ecchymosis
    for i in range(8):
        alpha = 0.6 - i * 0.07
        bx    = 200 + i * 15
        draw.ellipse(
            [bx, 300 + i*8, 1000 - i*15, 620 - i*8],
            fill=(120 - i*5, 80 - i*3, 140 - i*4)
        )

    # Laceration wound track — dark center
    # Draw as slightly irregular line
    points = []
    for x in range(220, 980, 8):
        y_offset = random.randint(-8, 8)
        points.append((x, 460 + y_offset))

    # Wound depth — dark subcutaneous layer
    for i, (px, py) in enumerate(points):
        width = random.randint(18, 28)
        draw.ellipse([px-4, py-width//2, px+4, py+width//2],
                     fill=(60, 20, 20))

    # Wound bed — subcutaneous fat (yellowish) and muscle (red)
    for i, (px, py) in enumerate(points[5:-5]):
        draw.ellipse([px-3, py-10, px+3, py+10],
                     fill=(180, 140, 60))
        if i % 3 == 0:
            draw.ellipse([px-2, py-6, px+2, py+6],
                         fill=(150, 30, 30))

    # Wound edges — ragged skin margins
    for i, (px, py) in enumerate(points):
        # Left edge
        ex = random.randint(-5, 5)
        draw.ellipse(
            [px-3, py-26+ex, px+3, py-18+ex],
            fill=(170, 120, 90)
        )
        # Right edge
        draw.ellipse(
            [px-3, py+18+ex, px+3, py+26+ex],
            fill=(170, 120, 90)
        )

    # Active bleeding — dark red pooling
    bleed_spots = [(350, 455), (580, 465), (750, 458), (900, 462)]
    for bx, by in bleed_spots:
        draw.ellipse([bx-20, by-12, bx+20, by+12], fill=(100, 15, 15))
        draw.ellipse([bx-12, by-7,  bx+12, by+7],  fill=(120, 20, 20))

    img = img.filter(ImageFilter.GaussianBlur(radius=0.9))
    img = noise_pixels(img, 0.03)
    img = add_image_label(img, "LACERATION - DEEP - RIGHT THIGH")

    path = str(OUTPUT_DIR / "laceration_deep.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── IMAGE 4: Crush Injury ────────────────────────────────
def generate_crush_injury():
    """
    Crush injury / severe contusion.
    Characteristics: extensive bruising, swelling, mottled
    discolouration, possible compartment syndrome signs.
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (195, 145, 110))
    draw = ImageDraw.Draw(img)

    # Base skin
    for _ in range(500):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        r = random.randint(2, 6)
        v = random.randint(-15, 15)
        draw.ellipse([x-r, y-r, x+r, y+r],
                     fill=(195+v, 145+v//2, 110+v//3))

    # Massive bruising / haematoma
    bruise_colors = [
        (80,  40, 100),
        (100, 50, 120),
        (120, 60, 90),
        (90,  45, 110),
        (70,  35, 85),
    ]
    for i, color in enumerate(bruise_colors):
        offset = i * 25
        draw.ellipse(
            [150 + offset, 200 + offset,
             1050 - offset, 700 - offset],
            fill=color
        )

    # Mottled pattern — skin breakdown
    for _ in range(200):
        mx = random.randint(200, 1000)
        my = random.randint(250, 650)
        mr = random.randint(8, 25)
        mottled_colors = [
            (60, 30, 80), (100, 50, 110),
            (140, 80, 50), (90, 60, 40)
        ]
        draw.ellipse(
            [mx-mr, my-mr, mx+mr, my+mr],
            fill=random.choice(mottled_colors)
        )

    # Swelling contour — limb appears larger
    draw.ellipse([100, 150, 1100, 750], outline=(150, 100, 80), width=5)

    # Skin tension lines
    for i in range(5):
        sx = random.randint(250, 900)
        sy = random.randint(300, 600)
        draw.line(
            [sx, sy, sx + random.randint(30, 80), sy + random.randint(5, 20)],
            fill=(170, 130, 100), width=2
        )

    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img = noise_pixels(img, 0.04)
    img = add_image_label(img, "CRUSH INJURY - RIGHT LEG - SEVERE CONTUSION")

    path = str(OUTPUT_DIR / "crush_injury_leg.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── IMAGE 5: Facial Burns (Inhalation Risk) ───────────────
def generate_facial_burns():
    """
    Facial burns with inhalation injury indicators.
    Critical visual cues: singed eyebrows/eyelashes area,
    perioral burns, soot deposits, mucosal erythema.
    Model must flag: INHALATION INJURY RISK → IMMEDIATE.
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (210, 165, 130))
    draw = ImageDraw.Draw(img)

    # Face outline
    draw.ellipse([200, 100, 1000, 850], fill=(205, 160, 125))

    # Normal skin texture
    for _ in range(400):
        x = random.randint(220, 980)
        y = random.randint(120, 830)
        r = random.randint(1, 4)
        v = random.randint(-12, 12)
        draw.ellipse([x-r, y-r, x+r, y+r],
                     fill=(205+v, 160+v//2, 125+v//3))

    # Eye regions — burned/singed
    for ex, ey in [(380, 340), (750, 340)]:
        draw.ellipse([ex-80, ey-30, ex+80, ey+30], fill=(160, 90, 60))
        draw.ellipse([ex-70, ey-22, ex+70, ey+22], fill=(140, 75, 50))
        # Singed eyebrow area — darker, burned hair follicles
        for _ in range(30):
            bx = random.randint(ex-70, ex+70)
            by = random.randint(ey-38, ey-25)
            draw.ellipse([bx-2, by-1, bx+2, by+1],
                         fill=(30, 20, 15))

    # Perioral burns — around mouth
    draw.ellipse([440, 580, 760, 720], fill=(180, 100, 70))
    draw.ellipse([470, 600, 730, 700], fill=(160, 85, 60))

    # Nasal area — singed nasal hairs, soot
    draw.ellipse([530, 450, 670, 570], fill=(190, 130, 95))
    # Soot deposits — black specks around nostrils
    for _ in range(60):
        sx = random.randint(530, 670)
        sy = random.randint(490, 580)
        draw.ellipse([sx-2, sy-2, sx+2, sy+2],
                     fill=(20, 15, 10))

    # Soot on forehead — carbon deposits from smoke
    for _ in range(120):
        fx = random.randint(280, 920)
        fy = random.randint(130, 320)
        fs = random.randint(1, 5)
        opacity = random.randint(20, 60)
        draw.ellipse([fx-fs, fy-fs, fx+fs, fy+fs],
                     fill=(opacity, opacity-5, opacity-10))

    # Erythema spreading from burn areas
    draw.ellipse([300, 280, 900, 780], outline=(200, 80, 60), width=6)

    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    img = noise_pixels(img, 0.035)
    img = add_image_label(img, "FACIAL BURNS - INHALATION INJURY RISK")

    path = str(OUTPUT_DIR / "burn_facial_inhalation.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── IMAGE 6: Normal Skin (Control) ───────────────────────
def generate_normal_skin():
    """
    Normal healthy skin — control image.
    Model should return: No significant injury visible. MINOR/reassess.
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (200, 155, 120))
    draw = ImageDraw.Draw(img)

    # Healthy skin texture
    for _ in range(1200):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        r = random.randint(1, 5)
        v = random.randint(-20, 20)
        draw.ellipse([x-r, y-r, x+r, y+r],
                     fill=(200+v, 155+v//2, 120+v//3))

    # Minor natural skin variations
    for _ in range(50):
        vx = random.randint(100, 1100)
        vy = random.randint(50, 850)
        vr = random.randint(5, 20)
        v  = random.randint(-25, 25)
        draw.ellipse([vx-vr, vy-vr, vx+vr, vy+vr],
                     fill=(200+v, 155+v//2, 120+v//3))

    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = noise_pixels(img, 0.02)
    img = add_image_label(img, "NORMAL SKIN - CONTROL IMAGE")

    path = str(OUTPUT_DIR / "normal_skin.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── IMAGE 7: Abrasion / Road Rash ────────────────────────
def generate_abrasion():
    """
    Road rash / abrasion — MINOR injury.
    Superficial skin loss, multiple small bleeding points.
    """
    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (198, 148, 112))
    draw = ImageDraw.Draw(img)

    # Skin background
    for _ in range(600):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        r = random.randint(1, 4)
        v = random.randint(-15, 15)
        draw.ellipse([x-r, y-r, x+r, y+r],
                     fill=(198+v, 148+v//2, 112+v//3))

    # Abrasion area — superficial skin loss
    draw.ellipse([250, 250, 950, 680], fill=(185, 100, 85))

    # Abraded surface — stippled red dots (petechiae / capillary bleeding)
    for _ in range(500):
        ax = random.randint(260, 940)
        ay = random.randint(260, 670)
        ar = random.randint(2, 7)
        red_var = random.randint(140, 200)
        draw.ellipse([ax-ar, ay-ar, ax+ar, ay+ar],
                     fill=(red_var, 40, 40))

    # Dirt / debris embedded
    for _ in range(80):
        dx = random.randint(280, 920)
        dy = random.randint(280, 660)
        dr = random.randint(1, 4)
        draw.ellipse([dx-dr, dy-dr, dx+dr, dy+dr],
                     fill=(40, 35, 25))

    # Partial skin tags at wound edges
    draw.ellipse([250, 250, 950, 680], outline=(160, 80, 70), width=3)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
    img = noise_pixels(img, 0.04)
    img = add_image_label(img, "ABRASION - ROAD RASH - MINOR")

    path = str(OUTPUT_DIR / "abrasion_road_rash.jpg")
    img.save(path, quality=92)
    print(f"  Generated: {path}")
    return path


# ── MAIN GENERATOR ────────────────────────────────────────
if __name__ == "__main__":
    from rich.console import Console
    from rich.panel  import Panel
    console = Console()

    console.print(Panel(
        "[bold cyan]Generating synthetic wound test images...[/bold cyan]\n"
        "These simulate visual characteristics for Gemma 4 vision testing.",
        border_style="cyan"
    ))

    generators = [
        ("Partial thickness burn",    generate_burn_partial),
        ("Full thickness burn",       generate_burn_full_thickness),
        ("Deep laceration",           generate_laceration_deep),
        ("Crush injury",              generate_crush_injury),
        ("Facial burns (inhalation)", generate_facial_burns),
        ("Normal skin (control)",     generate_normal_skin),
        ("Abrasion / road rash",      generate_abrasion),
    ]

    generated = []
    for name, fn in generators:
        console.print(f"  Generating: {name}...")
        try:
            path = fn()
            generated.append((name, path, True))
        except Exception as e:
            console.print(f"  [red]FAILED: {e}[/red]")
            generated.append((name, "", False))

    console.print("")
    console.print("[bold]Generated images:[/bold]")
    for name, path, ok in generated:
        status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        console.print(f"  {status} {name}")
        if ok:
            console.print(f"      → {path}")

    # Show all images in folder
    console.print(f"\n[cyan]All test images in data\\test_images\\:[/cyan]")
    for img_path in sorted(OUTPUT_DIR.glob("*.jpg")):
        size_kb = round(img_path.stat().st_size / 1024)
        console.print(f"  {img_path.name} ({size_kb} KB)")

    console.print(Panel(
        "[bold green]Test images generated.[/bold green]\n"
        "Proceed to Phase 4 — Build Vision Module.",
        border_style="green"
    ))