"""Build-time raster artwork; no SVG parsing or custom fonts on the MPC."""
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageChops


def svg_icon(path, size, colour, background):
    """Rasterize the supplied icon's M/L/H/V/C/Z paths with round strokes."""
    root = ET.parse(path).getroot()
    scale = size * 4 / float(root.attrib['viewBox'].split()[2])
    image = Image.new('RGB', (size * 4, size * 4), background)
    draw = ImageDraw.Draw(image)
    for element in root.findall('{http://www.w3.org/2000/svg}path'):
        tokens = re.findall(r'[MLHVCZ]|-?\d+(?:\.\d+)?', element.attrib['d'])
        points = []
        index = 0
        while index < len(tokens):
            command = tokens[index]
            index += 1
            if command in ('M', 'L'):
                points.append(tuple(float(v) for v in tokens[index:index + 2]))
                index += 2
            elif command in ('H', 'V'):
                x, y = points[-1]
                value = float(tokens[index])
                index += 1
                points.append((value, y) if command == 'H' else (x, value))
            elif command == 'C':
                values = [float(v) for v in tokens[index:index + 6]]
                index += 6
                a = points[-1]
                b, c, end = values[:2], values[2:4], values[4:]
                for step in range(1, 25):
                    t = step / 24
                    points.append(tuple((1-t)**3*a[k] + 3*(1-t)**2*t*b[k]
                                        + 3*(1-t)*t*t*c[k] + t**3*end[k]
                                        for k in (0, 1)))
            elif command == 'Z':
                points.append(points[0])
            else:
                raise ValueError('Unsupported icon path command: ' + command)
        width = round(float(element.attrib.get('stroke-width', 2)) * scale)
        scaled = [(x * scale, y * scale) for x, y in points]
        draw.line(scaled, fill=colour, width=width, joint='curve')
        radius = width / 2
        for x, y in scaled:
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=colour)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def wordmark(colour, background):
    """Original geometric AIRLINK lettering with an inset stripe."""
    scale = 4
    glyphs = {
        'A': [[(0,34),(0,0),(30,0),(30,34)],[(0,19),(30,19)]],
        'I': [[(0,0),(0,34)]],
        'R': [[(0,34),(0,0),(30,0),(30,17),(0,17)],[(15,17),(30,34)]],
        'L': [[(0,0),(0,34),(30,34)]],
        'N': [[(0,34),(0,0),(30,34),(30,0)]],
        'K': [[(0,0),(0,34)],[(30,0),(0,17),(30,34)]],
    }
    def stroke(draw, points, width, ink):
        # Uniform round caps keep every letter on the same cap and baseline.
        diameter = width * scale
        radius = diameter / 2
        draw.line(points, fill=ink, width=diameter, joint='curve')
        for px, py in points:
            draw.ellipse((px-radius, py-radius, px+radius, py+radius), fill=ink)
    letters = []
    for letter in 'AIRLINK':
        image = Image.new('RGB', (44*scale, 44*scale), background)
        draw = ImageDraw.Draw(image)
        paths = [[((px+6)*scale, (py+5)*scale) for px, py in points]
                 for points in glyphs[letter]]
        for width, ink in ((10, colour), (3, background)):
            for points in paths:
                stroke(draw, points, width, ink)
        # Space actual ink bounds, rather than each letter's advance width.
        bounds = ImageChops.difference(image, Image.new('RGB', image.size, background)).getbbox()
        width = 10 if letter == 'I' else 40
        letters.append(image.crop((bounds[0], 0, bounds[2], 44*scale)).resize(
            (width*scale, 44*scale), Image.Resampling.LANCZOS))
    gap = 8 * scale  # Same clear gap as the previous N-to-K spacing.
    result = Image.new('RGB', (sum(im.width for im in letters)+gap*6, 44*scale), background)
    x = 0
    for letter in letters:
        result.paste(letter, (x, 0))
        x += letter.width + gap
    return result.resize((result.width//scale, 44), Image.Resampling.LANCZOS)
