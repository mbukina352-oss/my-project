"""Генерирует axlev-estate.svg: надпись AXLEV ESTATE на тёмно-зелёном фоне
с полупрозрачным львом (голова анфас) на заднем плане."""
import math

CX, CY = 960, 560


def lock(angle, r_in, r_out, width, sweep):
    """Одна прядь гривы: изогнутый язычок от r_in к r_out."""
    def pt(r, a):
        return CX + r * math.cos(a), CY + r * math.sin(a)
    a_tip = angle + sweep
    b1 = pt(r_in, angle - width)
    b2 = pt(r_in, angle + width)
    tip = pt(r_out, a_tip)
    rm = (r_in + r_out) / 2
    c1 = pt(rm, angle - width * 1.1 + sweep * 0.2)
    c2 = pt(rm * 1.05, angle + width * 0.9 + sweep * 0.9)
    f = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    return f"M{f(b1)} Q{f(c1)} {f(tip)} Q{f(c2)} {f(b2)} Z"


def mane_layer(n, r_in, r_out_fn, width, sweep, rot=0.0):
    paths = []
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        paths.append(lock(a, r_in, r_out_fn(a), width, sweep))
    return " ".join(paths)


# грива длиннее по бокам и снизу, короче на макушке
def outer(base, amp):
    return lambda a: base + amp * (0.5 + 0.5 * math.sin(a))  # sin>0 — низ

mane_back = mane_layer(30, 250, outer(430, 90), 0.13, 0.16)
mane_mid = mane_layer(26, 240, outer(360, 70), 0.14, -0.14, rot=0.12)
mane_front = mane_layer(22, 230, outer(300, 40), 0.15, 0.12, rot=0.05)

c = CX
y = CY
face = (f"M{c},{y-235} C{c+100},{y-235} {c+185},{y-190} {c+200},{y-100} "
        f"C{c+215},{y-10} {c+195},{y+80} {c+140},{y+160} "
        f"C{c+100},{y+215} {c+55},{y+250} {c},{y+258} "
        f"C{c-55},{y+250} {c-100},{y+215} {c-140},{y+160} "
        f"C{c-195},{y+80} {c-215},{y-10} {c-200},{y-100} "
        f"C{c-185},{y-190} {c-100},{y-235} {c},{y-235} Z")
ears = (f"M{c-140},{y-195} C{c-185},{y-285} {c-265},{y-255} {c-215},{y-150} Z "
        f"M{c+140},{y-195} C{c+185},{y-285} {c+265},{y-255} {c+215},{y-150} Z")
brow = (f"M{c-160},{y-45} C{c-120},{y-100} {c-55},{y-95} {c-22},{y-55} "
        f"M{c+160},{y-45} C{c+120},{y-100} {c+55},{y-95} {c+22},{y-55}")
eyes = (f"M{c-140},{y-28} C{c-112},{y-58} {c-68},{y-55} {c-45},{y-25} "
        f"C{c-78},{y-10} {c-115},{y-12} {c-140},{y-28} Z "
        f"M{c+140},{y-28} C{c+112},{y-58} {c+68},{y-55} {c+45},{y-25} "
        f"C{c+78},{y-10} {c+115},{y-12} {c+140},{y-28} Z")
pupils = f'<circle cx="{c-88}" cy="{y-32}" r="9"/><circle cx="{c+88}" cy="{y-32}" r="9"/>'
bridge = (f"M{c-22},{y-55} C{c-30},{y} {c-40},{y+40} {c-58},{y+72} "
          f"M{c+22},{y-55} C{c+30},{y} {c+40},{y+40} {c+58},{y+72}")
nose = (f"M{c-62},{y+72} C{c-40},{y+60} {c+40},{y+60} {c+62},{y+72} "
        f"C{c+52},{y+102} {c+22},{y+118} {c},{y+122} "
        f"C{c-22},{y+118} {c-52},{y+102} {c-62},{y+72} Z")
muzzle = (f"M{c},{y+122} L{c},{y+150} "
          f"M{c},{y+150} C{c-30},{y+178} {c-80},{y+175} {c-108},{y+138} "
          f"M{c},{y+150} C{c+30},{y+178} {c+80},{y+175} {c+108},{y+138} "
          f"M{c-60},{y+205} C{c-25},{y+228} {c+25},{y+228} {c+60},{y+205}")
whisker_dots = "".join(
    f'<circle cx="{c + s * dx}" cy="{y + dy}" r="5"/>'
    for s in (-1, 1) for dx, dy in ((70, 112), (92, 128), (74, 146)))

GOLD = "#e6c77e"
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
  <defs>
    <style>@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&amp;display=swap');</style>
    <radialGradient id="bg" cx="50%" cy="48%" r="75%">
      <stop offset="0" stop-color="#1b4634"/>
      <stop offset="0.55" stop-color="#0e2c20"/>
      <stop offset="1" stop-color="#061710"/>
    </radialGradient>
    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f5e1a4"/>
      <stop offset="0.5" stop-color="#d6b166"/>
      <stop offset="1" stop-color="#a47e38"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#bg)"/>

  <!-- полупрозрачный лев -->
  <g opacity="0.13" stroke="{GOLD}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round">
    <path d="{mane_back}" fill="{GOLD}" fill-opacity="0.45"/>
    <path d="{mane_mid}" fill="{GOLD}" fill-opacity="0.3"/>
    <path d="{mane_front}" fill="{GOLD}" fill-opacity="0.2"/>
    <path d="{ears}" fill="{GOLD}" fill-opacity="0.5"/>
    <path d="{face}" fill="#0e2c20" fill-opacity="0.85"/>
    <path d="{brow}" fill="none"/>
    <path d="{eyes}" fill="{GOLD}" fill-opacity="0.6"/>
    <g fill="#0e2c20" stroke="none">{pupils}</g>
    <path d="{bridge}" fill="none"/>
    <path d="{nose}" fill="{GOLD}"/>
    <path d="{muzzle}" fill="none"/>
    <g fill="{GOLD}" stroke="none">{whisker_dots}</g>
  </g>

  <!-- надпись -->
  <g font-family="'Cormorant Garamond', 'Times New Roman', serif" text-anchor="middle" fill="url(#gold)">
    <text x="978" y="590" font-size="250" font-weight="600" letter-spacing="36">AXLEV</text>
    <rect x="700" y="648" width="520" height="2" fill="#d6b166"/>
    <text x="983" y="738" font-size="66" font-weight="500" letter-spacing="46">ESTATE</text>
  </g>
</svg>
'''
with open("axlev-estate.svg", "w") as fh:
    fh.write(svg)
