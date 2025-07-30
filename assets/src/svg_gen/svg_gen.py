#!/usr/bin/env python3
"""
SVG table generator for support matrix with sub-column support.

This module provides classes and functions to generate SVG tables with
color-coded cells, links, and HTML image maps. It's specialized for
support matrix tables but can be used for general SVG table generation.

If you want to use the original version, see: wychlw/plct/misc
"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
import logging
import tempfile
import threading
from typing import List, Optional, Union, Iterator, Protocol
from numbers import Number
from math import sqrt
import cairo

# Constants
DEFAULT_FONT_SIZE = 12
DEFAULT_FONT_FAMILY = 'Arial'
DEFAULT_STROKE_WIDTH = 2
DEFAULT_PADDING_X = 5
DEFAULT_PADDING_Y = 4
TEXT_WIDTH_SCALE_FACTOR = 1.5  # Scaling factor for text width calculation
LINE_HEIGHT_RATIO = 20 / 12  # Ratio for calculating line height from font size


class SvgConf:
    """
    Configuration for SVG table generation.
    
    This class holds all the styling and layout configuration for SVG tables,
    including font settings, stroke widths, and padding values.
    """

    def __init__(self, 
                 font_size: int = DEFAULT_FONT_SIZE, 
                 font_family: str = DEFAULT_FONT_FAMILY, 
                 stroke_width: int = DEFAULT_STROKE_WIDTH,
                 padding_x: int = DEFAULT_PADDING_X, 
                 padding_y: int = DEFAULT_PADDING_Y) -> None:
        """Initialize SVG configuration.
        
        Args:
            font_size: Font size in points
            font_family: Font family name
            stroke_width: Width of strokes/borders
            padding_x: Horizontal padding
            padding_y: Vertical padding
        """
        self.font_size = font_size
        self.font_family = font_family
        self.stroke_width = stroke_width
        self.padding_x = padding_x
        self.padding_y = padding_y
        self._text_width_cache = {}

    def line_height(self) -> float:
        """
        Calculate line height based on font size.
        
        Returns:
            Line height in the same units as font_size
        """
        return self.font_size * LINE_HEIGHT_RATIO

    @contextmanager
    def _create_cairo_surface(self):
        """Create a temporary Cairo surface for text measurement."""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            surface = cairo.SVGSurface(temp_path, 1280, 200)
            yield surface
        finally:
            surface.finish()
            try:
                import os
                os.unlink(temp_path)
            except OSError:
                logging.warning(f"Failed to remove temporary file: {temp_path}")

    def text_width(self, text: str, bold: bool = False) -> float:
        """
        Calculate the width of text when rendered.
        
        Args:
            text: Text to measure
            bold: Whether the text should be bold
            
        Returns:
            Width of the text in the same units as font_size
            
        Raises:
            RuntimeError: If Cairo operations fail
        """
        if not text:
            return 0.0
            
        # Use cache to avoid repeated Cairo operations
        cache_key = (text, bold, self.font_size, self.font_family)
        if cache_key in self._text_width_cache:
            return self._text_width_cache[cache_key]
        
        try:
            with self._create_cairo_surface() as surface:
                cr = cairo.Context(surface)
                cr.select_font_face(
                    self.font_family, 
                    cairo.FONT_SLANT_NORMAL,
                    cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
                )
                cr.set_font_size(self.font_size)
                _, _, width, _, _, _ = cr.text_extents(text)
                
                # Reason: Scale factor accounts for rendering differences and padding
                result = width * TEXT_WIDTH_SCALE_FACTOR
                self._text_width_cache[cache_key] = result
                return result
                
        except Exception as e:
            logging.error(f"Failed to calculate text width for '{text}': {e}")
            # Fallback to approximate calculation
            return len(text) * self.font_size * (0.7 if bold else 0.65)


class SvgConfManager:
    """
    Thread-safe singleton manager for SvgConf instances.
    
    This class provides a safe way to manage global SVG configuration
    while avoiding the pitfalls of traditional singleton patterns.
    """
    _instance: Optional['SvgConf'] = None
    _lock = threading.Lock()

    @classmethod
    def get_config(cls) -> 'SvgConf':
        """
        Get the current SVG configuration instance.
        
        Returns:
            Current SvgConf instance, creating default if none exists
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking
                    cls._instance = SvgConf()
        return cls._instance

    @classmethod
    def set_config(cls, conf: SvgConf) -> None:
        """
        Set a new SVG configuration instance.
        
        Args:
            conf: New SvgConf instance to use globally
        """
        if not isinstance(conf, SvgConf):
            raise TypeError("conf must be an instance of SvgConf")
        
        with cls._lock:
            cls._instance = conf

    @classmethod
    def reset_config(cls) -> None:
        """
        Reset configuration to default values.
        """
        with cls._lock:
            cls._instance = None


def getconf() -> SvgConf:
    """
    Get the current SVG configuration.
    
    Returns:
        Current SvgConf instance
    """
    return SvgConfManager.get_config()


def putconf(conf: SvgConf) -> None:
    """
    Set a new SVG configuration.
    
    Args:
        conf: New configuration to use
    
    Raises:
        TypeError: If conf is not an SvgConf instance
    """
    SvgConfManager.set_config(conf)


class SvgNode(ABC):
    """
    Abstract base class for all SVG nodes.
    
    This class provides the basic structure for building SVG elements
    in a tree-like structure with automatic layout calculation.
    """
    w: Number = 0
    h: Number = 0
    x1: Number = 0
    y1: Number = 0
    x2: Number = 0
    y2: Number = 0

    def __init__(self, conf: Optional[SvgConf] = None) -> None:
        """Initialize SVG node.
        
        Args:
            conf: SVG configuration to use. If None, uses global config.
        """
        self.children: List['SvgNode'] = []
        self.conf = conf or getconf()

    @abstractmethod
    def gen_begin(self) -> str:
        """
        Generate SVG content before children are rendered.
        
        Returns:
            SVG markup string
        """
        return ''

    @abstractmethod
    def gen_end(self) -> str:
        """
        Generate SVG content after children are rendered.
        
        Returns:
            SVG markup string
        """
        return ''

    def add_child(self, child: 'SvgNode') -> None:
        """
        Add a child node to this node.
        
        Args:
            child: Child node to add
            
        Raises:
            TypeError: If child is not an SvgNode instance
        """
        if not isinstance(child, SvgNode):
            raise TypeError("Child must be an SvgNode instance")
        self.children.append(child)

    def __str__(self) -> str:
        """
        Generate SVG markup for this node and its children.
        
        Returns:
            Complete SVG markup string
        """
        return self.generate()

    def walk(self) -> Iterator['SvgNode']:
        """
        Walk through the node tree in depth-first order.
        
        Yields:
            SvgNode: Each node in the tree
        """
        for child in self.children:
            yield from child.walk()
        yield self

    def width(self) -> Number:
        """
        Get the width of the node

        For a node with children, cursor xpos will be advanced when adding a new child
        """
        if len(self.children) == 0:
            return self.w
        widths = []
        n_width = 0
        for i in self.children:
            if isinstance(i, SvgMoveTo):
                widths.append(n_width)
                n_width = i.x
                continue
            if isinstance(i, SvgCR):
                widths.append(n_width)
                n_width = 0
                continue
            n_width += i.width()
        widths.append(n_width)
        return max(widths)

    def height(self) -> Number:
        """
        Get the height of the node

        Unlike width, ypos is not advanced when adding a new child
        """
        if len(self.children) == 0:
            return self.h
        heights = []
        s_heights = [] # Move to will reset the height, so we need to store the previous height
        n_height = 0
        for i in self.children:
            if isinstance(i, SvgMoveTo):
                heights.append(n_height)
                s_heights.append(sum(heights))
                heights = []
                n_height = i.y
                continue
            if isinstance(i, SvgLF):
                heights.append(n_height)
                n_height = 0
                continue
            n_height = max(n_height, i.height())
        heights.append(n_height)
        s_heights.append(sum(heights))
        return max(s_heights)

    def generate(self, xpos: Number = 0, ypos: Number = 0) -> str:
        """
        Generate the svg
        """
        self.x1 = xpos
        self.y1 = ypos
        self.h = self.height()
        self.w = self.width()
        self.x2 = xpos + self.w
        self.y2 = ypos + self.h

        res = ''
        res += self.gen_begin()
        n_width = 0
        n_height = 0
        for i in self.children:
            if isinstance(i, SvgMoveTo):
                xpos = i.x
                ypos = i.y
                n_width = i.x
                n_height = i.y
                continue
            if isinstance(i, SvgCR):
                xpos = 0
                n_width = 0
                continue
            if isinstance(i, SvgLF):
                ypos += n_height
                n_height = 0
                continue
            res += i.generate(xpos, ypos)
            n_width += i.width()
            n_height = max(n_height, i.height())
            xpos += i.width()
        res += self.gen_end()
        return res


class SvgAdvancer(SvgNode):
    """
    Move the cursor
    """

    def __init__(self, dx: Number, dy: Number):
        super().__init__()
        self.dx = dx
        self.dy = dy

    def gen_begin(self) -> str:
        return ''

    def gen_end(self) -> str:
        return ''

    def add_child(self, child):
        raise RuntimeError("Cannot add child to advancer!")

    def width(self) -> Number:
        return self.dx

    def height(self) -> Number:
        return self.dy


class SvgMoveTo(SvgNode):
    """
    Move the cursor to a specific position
    """

    def __init__(self, x: Number, y: Number):
        super().__init__()
        self.x = x
        self.y = y

    def gen_begin(self) -> str:
        return ''

    def gen_end(self) -> str:
        return ''

    def add_child(self, child):
        raise RuntimeError("Cannot add child to moveTo!")


class SvgCR(SvgNode):
    """
    Move cursor to the beginning of the line
    """

    def gen_begin(self) -> str:
        return ''

    def gen_end(self) -> str:
        return ''

    def add_child(self, child):
        raise RuntimeError("Cannot add child to CR!")


class SvgLF(SvgNode):
    """
    Move cursor to the next line
    """

    def gen_begin(self) -> str:
        return ''

    def gen_end(self) -> str:
        return ''

    def add_child(self, child):
        raise RuntimeError("Cannot add child to LF!")


class SvgXml(SvgNode):
    """
    Metadata for the svg
    """

    def gen_begin(self) -> str:
        return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'

    def gen_end(self) -> str:
        return ''


class SvgSvg(SvgNode):
    """
    The svg node
    """

    conf: SvgConf

    def __init__(self, _id='svg-chart'):
        super().__init__()
        self.id = _id

    def gen_begin(self) -> str:
        return f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '\
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '\
            f'id="{self.id}" font-family="{self.conf.font_family}" '\
            f'height="{self.h}" width="{self.w}" style="font-size: {self.conf.font_size}pt;">'

    def gen_end(self) -> str:
        return '</svg>'


class SvgGroup(SvgNode):
    """
    A group in the svg
    """

    def gen_begin(self) -> str:
        return '<g>'

    def gen_end(self) -> str:
        return '</g>'


class SvgLine(SvgNode):
    """
    A line in the svg
    """

    def __init__(self, dx: Number, dy: Number,
                 stroke_color: str = 'rgb(0,0,0)', stroke_width: Number = 1) -> None:
        super().__init__()
        self.dx = dx
        self.dy = dy
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.rat = self.stroke_width / sqrt(self.dx**2 + self.dy**2)

    def width(self) -> Number:
        return self.dx + self.dy * self.rat

    def height(self) -> Number:
        return self.dy + self.dx * self.rat

    def gen_begin(self) -> str:
        return f'<line x1="{self.x1 + self.dy * self.rat / 2}" '\
            f'y1="{self.y1 + self.dx * self.rat / 2}" '\
            f'x2="{self.x1 + self.dx + self.dy * self.rat / 2}" '\
            f'y2="{self.y1 + self.dy + self.dx * self.rat / 2}" '\
            f'style="stroke:{self.stroke_color};stroke-width:{self.stroke_width}"/>'

    def gen_end(self) -> str:
        return ''

    def add_child(self, child):
        raise RuntimeError("Cannot add child to line!")


class SvgText(SvgNode):
    """
    Some text in the svg
    """

    def __init__(self, text: str, blod=False):
        super().__init__()
        self.text = text
        self.blod = blod

    def height(self) -> Number:
        return self.conf.line_height() + self.conf.padding_y * 2

    def width(self) -> Number:
        return self.conf.text_width(self.text, self.blod) + self.conf.padding_x * 2

    def gen_begin(self) -> str:
        res = f'<text x="{self.x1 + self.conf.padding_x}" '\
            f'y="{self.y1 + self.h / 2}" '\
            f'class="table-data" '
        res += 'font-weight="bold" 'if self.blod else ''
        res += f'height="{self.h}" '\
            f'width="{self.conf.text_width(self.text)}">' \
            f'{self.text}'
        return res

    def gen_end(self) -> str:
        return '</text>'

    def add_child(self, child):
        raise RuntimeError("Cannot add child to text!")


class SvgTextCenter(SvgText):
    """
    Centered text, with given width
    """

    def __init__(self, text: str, width: Number, height: Number, blod=False):
        super().__init__(text)
        self.w = width
        self.h = height
        self.blod = blod

    def height(self) -> Number:
        return max(self.h, self.conf.line_height() + self.conf.padding_y * 2)

    def width(self) -> Number:
        return max(self.w, self.conf.text_width(self.text, self.blod) + self.conf.padding_x * 2)

    def gen_begin(self) -> str:
        text_width = self.conf.text_width(
            self.text, self.blod)
        dx_text_begin = self.w / 2 - text_width / 2
        res = f'<text x="{self.x1 + dx_text_begin}" '\
            f'y="{self.y1 + self.h / 2}" '
        res += 'font-weight="bold" 'if self.blod else ''
        res += f'class="table-data" '\
            f'height="{self.h}" '\
            f'width="{self.conf.text_width(self.text)}">' \
            f'{self.text}'
        return res

    def gen_end(self) -> str:
        return '</text>'

    def add_child(self, child):
        raise RuntimeError("Cannot add child to text!")


class SvgLink(SvgNode):
    """
    A link in the svg
    """

    def __init__(self, href: str):
        super().__init__()
        self.href = href

    def gen_begin(self) -> str:
        return f'<a xlink:href="{self.href}">'

    def gen_end(self) -> str:
        return '</a>'


class SvgRect(SvgNode):
    """
    A rectangle in the svg
    """

    def __init__(self, w: Number, h: Number, fill_color: str = 'rgb(0,0,0)') -> None:
        super().__init__()
        self.w = w
        self.h = h
        self.fill_color = fill_color

    def gen_begin(self) -> str:
        return f'<rect x="{self.x1}" y="{self.y1}" '\
            f'width="{self.w}" height="{self.h}" '\
            f'style="fill:{self.fill_color};"/>'

    def gen_end(self) -> str:
        return ''

    def add_child(self, child):
        raise RuntimeError("Cannot add child to rect!")


class SvgRectContainer(SvgNode):
    """
    Act as a background for the content of its children

    It's width and height is determined by the children
    """

    def __init__(self, fill_color: str = 'rgb(0,0,0)') -> None:
        super().__init__()
        self.fill_color = fill_color

    def gen_begin(self) -> str:
        return f'<rect x="{self.x1}" y="{self.y1}" '\
            f'width="{self.w}" height="{self.h}" '\
            f'style="fill:{self.fill_color};"/>'

    def gen_end(self) -> str:
        return ''


class MapNode(ABC):
    """
    A node in the html map
    """

    def __init__(self, alt: str, href: str) -> None:
        self.alt = alt
        self.href = href
        self.child = []

    @abstractmethod
    def before_str(self) -> str:
        """
        What to add before the child
        """
        raise RuntimeError("Sub class for shape!")

    @abstractmethod
    def after_str(self) -> str:
        """
        What to add after the child
        """
        raise RuntimeError("Sub class for shape!")

    def add_child(self, node):
        """
        Add a child node
        """
        self.child.append(node)

    def __str__(self) -> str:
        return self.before_str() + ''.join(map(str, self.child)) + self.after_str()


class PicMap(MapNode):
    """
    A simple map in the html
    """

    def __init__(self, _id: str, name: str) -> None:
        super().__init__("", "")
        self.id = _id
        self.name = name

    def before_str(self) -> str:
        return f'<map name="{self.name}" id="{self.name}">\n'

    def after_str(self) -> str:
        return '</map>\n'


class RectNode(MapNode):
    """
    A rectangle node in the html map
    """

    def __init__(self, x1, y1, x2, y2, alt: str, href: str) -> None:
        super().__init__(alt, href)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def before_str(self) -> str:
        return f'<area shape="rect" '\
            f'coords="{self.x1},{self.y1},{self.x2},{self.y2}"'\
            f'alt="{self.alt}" href="{self.href}">\n'

    def after_str(self) -> str:
        return ""


class CircleNode(MapNode):
    """
    A circle node in the html map
    """

    def __init__(self, x, y, r, alt: str, href: str) -> None:
        super().__init__(alt, href)
        self.x = x
        self.y = y
        self.r = r

    def before_str(self) -> str:
        return f'<area shape="circle" '\
            f'coords="{self.x},{self.y},{self.r}" '\
            f'alt="{self.alt}" href="{self.href}">\n'

    def after_str(self) -> str:
        return ""


class PolyNode(MapNode):
    """
    A polygon node in the html map
    """

    def __init__(self, points, alt: str, href: str) -> None:
        super().__init__(alt, href)
        self.points = points

    def before_str(self) -> str:
        return f'<area shape="poly" coords="{self.points}" alt="{self.alt}" href="{self.href}">\n'

    def after_str(self) -> str:
        return ""


def gen_html(svg: SvgNode, path: str) -> str:
    """
    Generate html from svg, with a map containing all the links, 
    pos coords are calculated by the svg node
    """
    mp = PicMap("svg_map", "svg_map")
    for i in svg.walk():
        if isinstance(i, SvgLink):
            href = i.href
            name = href.split('/')[-1]
            mp.add_child(RectNode(i.x1, i.y1, i.x2, i.y2, name, href))
    map_str = str(mp)
    html = f"""
<!DOCTYPE html>
<html>
<body>
<img src="{path}" usemap="#svg_map" />
{map_str}
</body>
</html>
"""
    return html
