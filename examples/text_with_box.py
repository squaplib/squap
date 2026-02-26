"""
Text Customisation
==================

Shows all text customisation options.
"""
import squap
from squap import var


def update_font():
    var.font.set_data(
        font=var.font_name, fs=var.font_size, bold=var.bold, italic=var.italic, underline=var.underline,
        strikethrough=var.strikeout, overline=var.overline, kerning=var.kerning, stretch=var.stretch,
        letter_spacing=var.letter_spacing, word_spacing=var.word_spacing)

    text.set_font(var.font)


def update_text():
    kwargs = {}
    if var.border_color is not None:
        kwargs['border_color'] = var.border_color
    if var.fill_color is not None:
        kwargs['fill_color'] = var.fill_color
    if var.border_width is not None:
        kwargs['border_width'] = var.border_width
    text.set_data(var.text, (var.x_pos, var.y_pos), angle=var.angle, c=var.color, **kwargs)


def reset_font():
    defaults = ["Segoe UI", 11, False, False, False, False, False, False, 100, 0.0, 0.0, False]
    for i in range(len(defaults)):
        font_boxes[i].set_value(defaults[i])


text = squap.plot_text("Hello World!", (0, 0))

text_tab = squap.add_input_table("text")
font_tab = squap.add_input_table("font")

text_tab.add_inputbox("text", "Hello World!").bind(update_text)
text_tab.add_slider("x-pos", 0, -1, 1, var_name="x_pos").bind(update_text)
text_tab.add_slider("y-pos", 0, -1, 1, var_name="y_pos").bind(update_text)
text_tab.add_slider("angle", 0, -180, 180).bind(update_text)
text_tab.add_color_picker("color", "red").bind(update_text)
text_tab.add_color_picker("fill color", None, var_name="fill_color").bind(update_text)
# !! to change this alpha has to be set higher than 0.

text_tab.add_color_picker("border color", "white", var_name="border_color").bind(update_text)
text_tab.add_inputbox("border width", 2, var_name="border_width").bind(update_text)

font_boxes = [
    font_tab.add_inputbox("font_name", "Segoe UI"),
    font_tab.add_slider("font_size", 20, 1, 50, only_ints=True, print_value=True),
    font_tab.add_inputbox("bold", False),
    font_tab.add_checkbox("italic", False),
    font_tab.add_checkbox("underline", False),
    font_tab.add_checkbox("strikeout", False),
    font_tab.add_checkbox("overline", False),
    font_tab.add_checkbox("kerning", False),
    font_tab.add_slider("stretch", 100, 1, 4000, logscale=True, only_ints=True, print_value=True),
    font_tab.add_inputbox("letter_spacing", 0.0),
    font_tab.add_inputbox("word_spacing", 0.0),
]
for box in font_boxes:
    box.bind(update_font)
font_tab.add_button("reset", reset_font)

squap.set_xlim(-1, 1)
squap.set_ylim(-1, 1)
squap.plot([-1, 1], [-1, 0.5])
squap.grid()

var.font = squap.get_font()
update_font()
update_text()

squap.show()
