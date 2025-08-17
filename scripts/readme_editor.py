#!/usr/bin/env python3
"""
Legacy README Editor script retained for reference.
This repository's primary application is Requirements to Test.
"""

import wx
import wx.html
import os
import re
import sys
import webbrowser
from typing import Optional
try:
    import markdown
    from markdown.extensions import codehilite, tables, toc, fenced_code
    try:
        import pymdown.extensions.superfences
        import pymdown.extensions.highlight
        import pymdown.extensions.inlinehilite
        import pymdown.extensions.magiclink
        import pymdown.extensions.betterem
        import pymdown.extensions.tasklist
        PYMDOWN_AVAILABLE = True
    except ImportError:
        PYMDOWN_AVAILABLE = False
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    PYMDOWN_AVAILABLE = False
try:
    # Running package-import style
    from .structured_template import create_readme_template, populate_tree_ctrl, ReadmeSection  # type: ignore
except Exception:
    # Fallback when running this file directly
    from structured_template import create_readme_template, populate_tree_ctrl, ReadmeSection  # type: ignore


class CustomColorDialog(wx.Dialog):
    """Custom color picker dialog with RGB sliders since wx.ColourDialog is broken on macOS"""
    
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(400, 300))
        
        self.color = wx.Colour(0, 0, 0)  # Default black
        
        # Create main panel
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Color preview
        self.color_preview = wx.Panel(panel, size=(100, 50))
        self.color_preview.SetBackgroundColour(self.color)
        
        # RGB sliders
        slider_sizer = wx.FlexGridSizer(3, 3, 5, 5)
        
        # Red slider
        slider_sizer.Add(wx.StaticText(panel, label="Red:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.red_slider = wx.Slider(panel, value=0, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.red_text = wx.StaticText(panel, label="0")
        slider_sizer.Add(self.red_slider, 1, wx.EXPAND)
        slider_sizer.Add(self.red_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Green slider
        slider_sizer.Add(wx.StaticText(panel, label="Green:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.green_slider = wx.Slider(panel, value=0, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.green_text = wx.StaticText(panel, label="0")
        slider_sizer.Add(self.green_slider, 1, wx.EXPAND)
        slider_sizer.Add(self.green_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Blue slider
        slider_sizer.Add(wx.StaticText(panel, label="Blue:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.blue_slider = wx.Slider(panel, value=0, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.blue_text = wx.StaticText(panel, label="0")
        slider_sizer.Add(self.blue_slider, 1, wx.EXPAND)
        slider_sizer.Add(self.blue_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        slider_sizer.AddGrowableCol(1)
        
        # Preset colors
        preset_sizer = wx.WrapSizer()
        presets = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (0, 0, 0),      # Black
            (128, 128, 128), # Gray
            (255, 255, 255), # White
        ]
        
        for r, g, b in presets:
            btn = wx.Button(panel, size=(30, 30))
            btn.SetBackgroundColour(wx.Colour(r, g, b))
            btn.Bind(wx.EVT_BUTTON, lambda evt, color=(r, g, b): self.on_preset_color(color))
            preset_sizer.Add(btn, 0, wx.ALL, 2)
        
        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(panel, wx.ID_OK)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        
        # Layout
        sizer.Add(wx.StaticText(panel, label="Color Preview:"), 0, wx.ALL, 5)
        sizer.Add(self.color_preview, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(slider_sizer, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(wx.StaticText(panel, label="Presets:"), 0, wx.ALL, 5)
        sizer.Add(preset_sizer, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(sizer)
        
        # Bind events
        self.red_slider.Bind(wx.EVT_SLIDER, self.on_slider_change)
        self.green_slider.Bind(wx.EVT_SLIDER, self.on_slider_change)
        self.blue_slider.Bind(wx.EVT_SLIDER, self.on_slider_change)
        
    def on_slider_change(self, event):
        """Update color when sliders change"""
        r = self.red_slider.GetValue()
        g = self.green_slider.GetValue()
        b = self.blue_slider.GetValue()
        
        self.color = wx.Colour(r, g, b)
        self.color_preview.SetBackgroundColour(self.color)
        self.color_preview.Refresh()
        
        self.red_text.SetLabel(str(r))
        self.green_text.SetLabel(str(g))
        self.blue_text.SetLabel(str(b))
        
    def on_preset_color(self, rgb):
        """Set color from preset button"""
        r, g, b = rgb
        self.red_slider.SetValue(r)
        self.green_slider.SetValue(g)
        self.blue_slider.SetValue(b)
        self.on_slider_change(None)
        
    def set_color(self, color):
        """Set the initial color"""
        self.color = color
        self.red_slider.SetValue(color.Red())
        self.green_slider.SetValue(color.Green())
        self.blue_slider.SetValue(color.Blue())
        self.on_slider_change(None)
        
    def get_color(self):
        """Get the selected color"""
        return self.color


class ReadmeEditorApp(wx.App):
    """Main application class"""

    def OnInit(self):
        frame = MainFrame()
        frame.Show()
        return True


class MainFrame(wx.Frame):
    """Main application window"""

    def __init__(self):
        super().__init__(None, title="README Editor", size=(1200, 800))

        # Initialize variables
        self.current_file = None
        self.is_modified = False
        self.preview_visible = False

        # Create UI components
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.create_main_panel()

        # Center the window
        self.Center()

        # Bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Set up accelerator table for keyboard shortcuts
        self.setup_accelerators()

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCtrl+N", "Create a new README file")
        file_menu.Append(wx.ID_OPEN, "&Open\tCtrl+O",
                         "Open an existing README file")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current file")
        file_menu.Append(wx.ID_SAVEAS, "Save &As\tCtrl+Shift+S",
                         "Save with a new name")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
        menubar.Append(file_menu, "&File")

        # Edit menu
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z", "Undo last action")
        edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y", "Redo last action")
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "Cut selected text")
        edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy selected text")
        edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V",
                         "Paste text from clipboard")
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A",
                         "Select all text")
        menubar.Append(edit_menu, "&Edit")

        # View menu
        view_menu = wx.Menu()
        self.general_view_item = view_menu.AppendRadioItem(
            wx.ID_ANY, "&General Editor", "Switch to general editor view")
        self.structured_view_item = view_menu.AppendRadioItem(
            wx.ID_ANY, "&Structured Editor",
            "Switch to structured project editor view")
        view_menu.AppendSeparator()
        self.preview_toggle_item = view_menu.AppendCheckItem(
            wx.ID_ANY, "&Preview Panel\tF12", "Toggle markdown preview panel")
        self.toc_link_toggle_item = view_menu.AppendCheckItem(
            wx.ID_ANY, "&Link headers to TOC", "Append [Table of Contents] link to each header")
        menubar.Append(view_menu, "&View")

        # Format menu
        format_menu = wx.Menu()

        # Headers submenu
        headers_menu = wx.Menu()
        self.h1_item = headers_menu.Append(wx.ID_ANY,
                                           "&H1 - Main Title\tCtrl+1",
                                           "Insert H1 header")
        self.h2_item = headers_menu.Append(wx.ID_ANY, "&H2 - Section\tCtrl+2",
                                           "Insert H2 header")
        self.h3_item = headers_menu.Append(wx.ID_ANY,
                                           "&H3 - Subsection\tCtrl+3",
                                           "Insert H3 header")
        self.h4_item = headers_menu.Append(wx.ID_ANY,
                                           "&H4 - Minor heading\tCtrl+4",
                                           "Insert H4 header")
        self.h5_item = headers_menu.Append(wx.ID_ANY,
                                           "&H5 - Small heading\tCtrl+5",
                                           "Insert H5 header")
        self.h6_item = headers_menu.Append(wx.ID_ANY,
                                           "&H6 - Tiny heading\tCtrl+6",
                                           "Insert H6 header")
        format_menu.AppendSubMenu(headers_menu, "&Headers")

        format_menu.AppendSeparator()

        # Text formatting
        self.bold_item = format_menu.Append(wx.ID_ANY, "&Bold\tCtrl+B",
                                            "Make text bold")
        self.italic_item = format_menu.Append(wx.ID_ANY, "&Italic\tCtrl+I",
                                              "Make text italic")
        self.strikethrough_item = format_menu.Append(
            wx.ID_ANY, "&Strikethrough\tCtrl+Shift+X", "Strikethrough text")
        self.inline_code_item = format_menu.Append(wx.ID_ANY,
                                                   "Inline &Code\tCtrl+`",
                                                   "Format as inline code")

        format_menu.AppendSeparator()

        # Blocks
        self.code_block_item = format_menu.Append(wx.ID_ANY,
                                                  "Code &Block\tCtrl+Shift+C",
                                                  "Insert code block")
        self.blockquote_item = format_menu.Append(wx.ID_ANY,
                                                  "Block&quote\tCtrl+Shift+>",
                                                  "Insert blockquote")
        self.hr_item = format_menu.Append(wx.ID_ANY,
                                          "&Horizontal Rule\tCtrl+Shift+-",
                                          "Insert horizontal rule")

        format_menu.AppendSeparator()

        # Lists
        self.ul_item = format_menu.Append(wx.ID_ANY,
                                          "&Unordered List\tCtrl+Shift+8",
                                          "Insert unordered list")
        self.ol_item = format_menu.Append(wx.ID_ANY,
                                          "O&rdered List\tCtrl+Shift+7",
                                          "Insert ordered list")
        self.task_list_item = format_menu.Append(wx.ID_ANY,
                                                 "&Task List\tCtrl+Shift+T",
                                                 "Insert task list")

        format_menu.AppendSeparator()

        # Links and references
        self.link_item = format_menu.Append(wx.ID_ANY, "&Link\tCtrl+K",
                                            "Insert link")
        self.image_item = format_menu.Append(wx.ID_ANY, "I&mage\tCtrl+Shift+I",
                                             "Insert image")

        format_menu.AppendSeparator()

        # Tables
        self.table_item = format_menu.Append(wx.ID_ANY, "&Table\tCtrl+T",
                                             "Insert table")

        menubar.Append(format_menu, "&Format")

        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About", "About README Editor")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_save_as, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU, self.on_redo, id=wx.ID_REDO)
        self.Bind(wx.EVT_MENU, self.on_cut, id=wx.ID_CUT)
        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.on_select_all, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_general_view, self.general_view_item)
        self.Bind(wx.EVT_MENU, self.on_structured_view,
                  self.structured_view_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_preview,
                  self.preview_toggle_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_toc_links, self.toc_link_toggle_item)

        # Format menu bindings
        self.Bind(wx.EVT_MENU, lambda evt: self.insert_header(1), self.h1_item)
        self.Bind(wx.EVT_MENU, lambda evt: self.insert_header(2), self.h2_item)
        self.Bind(wx.EVT_MENU, lambda evt: self.insert_header(3), self.h3_item)
        self.Bind(wx.EVT_MENU, lambda evt: self.insert_header(4), self.h4_item)
        self.Bind(wx.EVT_MENU, lambda evt: self.insert_header(5), self.h5_item)
        self.Bind(wx.EVT_MENU, lambda evt: self.insert_header(6), self.h6_item)
        self.Bind(wx.EVT_MENU, self.on_bold, self.bold_item)
        self.Bind(wx.EVT_MENU, self.on_italic, self.italic_item)
        self.Bind(wx.EVT_MENU, self.on_strikethrough, self.strikethrough_item)
        self.Bind(wx.EVT_MENU, self.on_inline_code, self.inline_code_item)
        self.Bind(wx.EVT_MENU, self.on_code_block, self.code_block_item)
        self.Bind(wx.EVT_MENU, self.on_blockquote, self.blockquote_item)
        self.Bind(wx.EVT_MENU, self.on_horizontal_rule, self.hr_item)
        self.Bind(wx.EVT_MENU, self.on_unordered_list, self.ul_item)
        self.Bind(wx.EVT_MENU, self.on_ordered_list, self.ol_item)
        self.Bind(wx.EVT_MENU, self.on_task_list, self.task_list_item)
        self.Bind(wx.EVT_MENU, self.on_link, self.link_item)
        self.Bind(wx.EVT_MENU, self.on_image, self.image_item)
        self.Bind(wx.EVT_MENU, self.on_table, self.table_item)
        # Appearance actions
        self.set_font_item = wx.MenuItem(format_menu, wx.ID_ANY, "Set &Font...\tCtrl+Shift+F")
        self.set_text_color_item = wx.MenuItem(format_menu, wx.ID_ANY, "Set &Text Color...\tCtrl+Shift+T")
        self.set_bg_color_item = wx.MenuItem(format_menu, wx.ID_ANY, "Set &Background Color...\tCtrl+Shift+B")
        self.clear_formatting_item = wx.MenuItem(format_menu, wx.ID_ANY, "&Clear Formatting\tCtrl+Shift+R")
        format_menu.AppendSeparator()
        format_menu.Append(self.set_font_item)
        format_menu.Append(self.set_text_color_item)
        format_menu.Append(self.set_bg_color_item)
        format_menu.Append(self.clear_formatting_item)
        self.Bind(wx.EVT_MENU, self.on_set_editor_font, self.set_font_item)
        self.Bind(wx.EVT_MENU, self.on_set_text_color, self.set_text_color_item)
        self.Bind(wx.EVT_MENU, self.on_set_background_color, self.set_bg_color_item)
        self.Bind(wx.EVT_MENU, self.on_clear_formatting, self.clear_formatting_item)

    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = self.CreateToolBar()

        # Add toolbar buttons
        toolbar.AddTool(wx.ID_NEW, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW),
                        "New file")
        toolbar.AddTool(wx.ID_OPEN, "Open",
                        wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN),
                        "Open file")
        toolbar.AddTool(wx.ID_SAVE, "Save",
                        wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE),
                        "Save file")
        toolbar.AddSeparator()
        toolbar.AddTool(wx.ID_UNDO, "Undo",
                        wx.ArtProvider.GetBitmap(wx.ART_UNDO), "Undo")
        toolbar.AddTool(wx.ID_REDO, "Redo",
                        wx.ArtProvider.GetBitmap(wx.ART_REDO), "Redo")
        toolbar.AddSeparator()

        # Preview toggle
        self.preview_toggle_tool = toolbar.AddCheckTool(
            wx.ID_ANY,
            "Preview",
            wx.ArtProvider.GetBitmap(wx.ART_FIND),
            shortHelp="Toggle Preview Panel")

        # Bind toolbar events
        self.Bind(wx.EVT_TOOL, self.on_toggle_preview,
                  self.preview_toggle_tool)

        toolbar.Realize()

    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText("Ready")

    def create_main_panel(self):
        """Create the main panel with editors"""
        self.main_panel = wx.Panel(self)

        # Create main splitter for editor and preview
        self.main_splitter = wx.SplitterWindow(self.main_panel,
                                               style=wx.SP_3D
                                               | wx.SP_LIVE_UPDATE)

        # Create notebook for different views
        self.notebook = wx.Notebook(self.main_splitter)

        # Create general editor
        self.general_editor = GeneralEditor(self.notebook, self)
        self.notebook.AddPage(self.general_editor, "General Editor")

        # Create structured editor
        self.structured_editor = StructuredEditor(self.notebook, self)
        self.notebook.AddPage(self.structured_editor, "Structured Editor")

        # Bind notebook page change event for content synchronization
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

        # Create preview panel
        self.preview_panel = self.create_preview_panel(self.main_splitter)

        # Initially show only the notebook (no preview)
        self.main_splitter.Initialize(self.notebook)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.main_splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.main_panel.SetSizer(sizer)

        # Bind notebook events
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

        # Set general editor as default
        self.general_view_item.Check()

    def setup_accelerators(self):
        """Set up keyboard accelerators"""
        # Create accelerator table for all shortcuts
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_F12, self.preview_toggle_item.GetId()),
            # Headers
            (wx.ACCEL_CTRL, ord('1'), self.h1_item.GetId()),
            (wx.ACCEL_CTRL, ord('2'), self.h2_item.GetId()),
            (wx.ACCEL_CTRL, ord('3'), self.h3_item.GetId()),
            (wx.ACCEL_CTRL, ord('4'), self.h4_item.GetId()),
            (wx.ACCEL_CTRL, ord('5'), self.h5_item.GetId()),
            (wx.ACCEL_CTRL, ord('6'), self.h6_item.GetId()),
            # Text formatting
            (wx.ACCEL_CTRL, ord('B'), self.bold_item.GetId()),
            (wx.ACCEL_CTRL, ord('I'), self.italic_item.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('X'),
             self.strikethrough_item.GetId()),
            (wx.ACCEL_CTRL, ord('`'), self.inline_code_item.GetId()),
            # Blocks
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('C'),
             self.code_block_item.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('.'),
             self.blockquote_item.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('-'), self.hr_item.GetId()),
            # Lists
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('8'), self.ul_item.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('7'), self.ol_item.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('T'),
             self.task_list_item.GetId()),
            # Links and references
            (wx.ACCEL_CTRL, ord('K'), self.link_item.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('I'),
             self.image_item.GetId()),
            # Tables
            (wx.ACCEL_CTRL, ord('T'), self.table_item.GetId()),
        ])
        self.SetAcceleratorTable(accelerator_table)

    def create_preview_panel(self, parent):
        """Create the markdown preview panel"""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Preview label
        label = wx.StaticText(panel, label="Markdown Preview:")
        sizer.Add(label, 0, wx.ALL, 5)

        # HTML window for preview
        self.preview_html = wx.html.HtmlWindow(panel)
        self.preview_html.SetPage(
            "<html><body><p>Preview will appear here...</p></body></html>")

        # Enable link clicking
        self.preview_html.Bind(wx.html.EVT_HTML_LINK_CLICKED,
                               self.on_link_clicked)

        sizer.Add(self.preview_html, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

        return panel

    def on_link_clicked(self, event):
        """Handle link clicks in preview"""
        link = event.GetLinkInfo()
        href = link.GetHref()

        # Handle internal anchor links (start with #)
        if href.startswith('#'):
            self.navigate_to_anchor(href)
        # Handle external links
        elif href.startswith(('http://', 'https://', 'mailto:')):
            webbrowser.open(href)
        else:
            # For other relative links, try to open in browser
            webbrowser.open(href)

    def navigate_to_anchor(self, anchor_href):
        """Navigate to a specific anchor within the preview"""
        # Remove the # prefix
        anchor_id = anchor_href[1:] if anchor_href.startswith(
            '#') else anchor_href

        # Convert anchor to match our section naming (GitHub-style)
        # This should match the get_anchor_id method in ReadmeSection
        target_anchor = anchor_id.lower().replace('-', '-')

        # Find the matching section in our template
        if hasattr(
                self,
                'structured_editor') and self.structured_editor.template_root:
            target_section = self.find_section_by_anchor(
                self.structured_editor.template_root, target_anchor)
            if target_section:
                # If we found the section, scroll to it using JavaScript
                self.scroll_to_section_in_preview(target_anchor)

                # Optionally, also select the section in the tree for better UX
                if hasattr(self.structured_editor, 'item_to_section'):
                    for item, section in self.structured_editor.item_to_section.items(
                    ):
                        if section == target_section:
                            self.structured_editor.tree_ctrl.SelectItem(item)
                            # Switch to structured editor if not already active
                            current_page = self.notebook.GetSelection()
                            if current_page != 1:  # Structured editor is page 1
                                self.notebook.SetSelection(1)
                            break

                # Update status
                self.status_bar.SetStatusText(
                    f"Navigated to section: {target_section.name}")
            else:
                # If section not found, just scroll to top
                self.scroll_to_section_in_preview("top")
                self.status_bar.SetStatusText(
                    f"Section '{anchor_id}' not found, scrolled to top")
        else:
            # Fallback: try to scroll using the anchor directly
            self.scroll_to_section_in_preview(target_anchor)

    def find_section_by_anchor(self, section, target_anchor):
        """Recursively find a section by its anchor ID"""
        # Check current section
        if section.get_anchor_id() == target_anchor:
            return section

        # Check children
        for child in section.children:
            result = self.find_section_by_anchor(child, target_anchor)
            if result:
                return result

        return None

    def scroll_to_section_in_preview(self, anchor_id):
        """Scroll to a specific section in the HTML preview using JavaScript"""
        if hasattr(self, 'preview_html'):
            # JavaScript to scroll to the anchor
            if anchor_id == "top":
                js_code = "window.scrollTo(0, 0);"
            else:
                # Try multiple common anchor formats
                js_code = f"""
                var element = document.getElementById('{anchor_id}') || 
                             document.querySelector('a[name="{anchor_id}"]') ||
                             document.querySelector('h1, h2, h3, h4, h5, h6').querySelector('[id*="{anchor_id}"]');
                if (element) {{
                    element.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                    // Highlight the section briefly
                    element.style.backgroundColor = '#ffff99';
                    setTimeout(function() {{ 
                        element.style.backgroundColor = ''; 
                    }}, 2000);
                }} else {{
                    // Try finding by text content
                    var headers = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    for (var i = 0; i < headers.length; i++) {{
                        var headerText = headers[i].textContent.toLowerCase().replace(/[^a-z0-9]/g, '-');
                        if (headerText.includes('{anchor_id}'.replace('-', '')) || 
                            headerText.replace(/-+/g, '-') === '{anchor_id}') {{
                            headers[i].scrollIntoView({{behavior: 'smooth', block: 'start'}});
                            headers[i].style.backgroundColor = '#ffff99';
                            setTimeout(function() {{ 
                                headers[i].style.backgroundColor = ''; 
                            }}, 2000);
                            break;
                        }}
                    }}
                }}
                """

            # Execute JavaScript in the HTML window (if supported)
            try:
                # Note: wx.html.HtmlWindow doesn't support JavaScript execution
                # This is a limitation we'll work around by using anchor navigation
                self.preview_html.ScrollToAnchor(anchor_id)
            except:
                # If scrolling fails, just update status
                self.status_bar.SetStatusText(
                    f"Navigation attempted to: {anchor_id}")
                pass

    def get_current_editor(self):
        """Get the currently active editor"""
        page = self.notebook.GetCurrentPage()
        return page

    def on_page_changed(self, event):
        """Handle page change in notebook"""
        page = event.GetSelection()
        if page == 0:
            self.general_view_item.Check()
        else:
            self.structured_view_item.Check()
        event.Skip()

    def on_general_view(self, event):
        """Switch to general editor view"""
        self.notebook.SetSelection(0)

    def on_structured_view(self, event):
        """Switch to structured editor view"""
        self.notebook.SetSelection(1)

    def on_page_changed(self, event):
        """Handle notebook page changes to synchronize content between editors"""
        old_page = event.GetOldSelection()
        new_page = event.GetSelection()

        # Only synchronize if switching between different editors (not on initial load)
        if old_page != -1:
            # Synchronize content when switching between editors
            if old_page == 1 and new_page == 0:
                # Switching from structured to general editor
                # Get the generated markdown from structured editor
                structured_content = self.structured_editor.get_content()
                self.general_editor.load_content(structured_content)
                self.status_bar.SetStatusText(
                    "Synchronized structured content to general editor")

            elif old_page == 0 and new_page == 1:
                # Switching from general to structured editor
                # Get content from general editor and try to parse it
                general_content = self.general_editor.get_content()
                self.structured_editor.load_content(general_content)
                self.status_bar.SetStatusText(
                    "Synchronized general content to structured editor")

        # Update preview if visible
        if self.preview_visible:
            wx.CallAfter(self.update_preview)
        
        # Update the window title to reflect the current editor mode
        self.update_title()

        event.Skip()

    def on_toggle_preview(self, event):
        """Toggle the preview panel"""
        self.preview_visible = not self.preview_visible

        if self.preview_visible:
            # Show preview panel
            if self.main_splitter.IsSplit():
                self.main_splitter.Unsplit()
            self.main_splitter.SplitVertically(self.notebook,
                                               self.preview_panel, -400)
            self.main_splitter.SetMinimumPaneSize(200)
            self.update_preview()
        else:
            # Hide preview panel
            if self.main_splitter.IsSplit():
                self.main_splitter.Unsplit()
            self.main_splitter.Initialize(self.notebook)

        # Update menu item and toolbar
        self.preview_toggle_item.Check(self.preview_visible)
        if hasattr(self, 'preview_toggle_tool'):
            toolbar = self.GetToolBar()
            toolbar.ToggleTool(self.preview_toggle_tool.GetId(),
                               self.preview_visible)

    def apply_editor_appearance(self):
        """Apply stored appearance to editors"""
        font = getattr(self, 'editor_font', None)
        text_colour = getattr(self, 'editor_text_colour', None)
        bg_colour = getattr(self, 'editor_background_colour', None)
        
        if hasattr(self, 'general_editor') and self.general_editor:
            self.general_editor.apply_appearance(font, text_colour, bg_colour)
        if hasattr(self, 'structured_editor') and self.structured_editor:
            self.structured_editor.apply_appearance(font, text_colour, bg_colour)

    def on_set_editor_font(self, event):
        """Open font dialog to set editor font"""
        dlg = wx.FontDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            chosen = data.GetChosenFont()
            self.editor_font = self._normalize_font_for_macos(chosen)
            self.apply_editor_appearance()
            self.set_modified()
        dlg.Destroy()

    def on_set_text_color(self, event):
        """Open custom color picker for text color"""
        dlg = CustomColorDialog(self, "Choose Text Color")
        if hasattr(self, 'editor_text_colour') and self.editor_text_colour:
            dlg.set_color(self.editor_text_colour)
        
        if dlg.ShowModal() == wx.ID_OK:
            color = dlg.get_color()
            self.editor_text_colour = color
            self.apply_editor_appearance()
            self.set_modified()
        dlg.Destroy()

    def _normalize_font_for_macos(self, font: wx.Font) -> wx.Font:
        """Avoid CoreText warnings by remapping hidden macOS UI font names.

        Some system fonts (e.g. '.SFNS-Regular') are private CoreText names.
        If selected, rebuild a similar wx.Font using system GUI family
        without a private face name.
        """
        try:
            if sys.platform == 'darwin':
                face = font.GetFaceName() or ""
                if face.startswith('.') or 'SFNS' in face:
                    # Build a new font with same metrics but generic family
                    size = font.GetPointSize()
                    style = font.GetStyle()
                    weight = font.GetWeight()
                    underline = font.GetUnderlined()
                    # Prefer the default GUI font family
                    sys_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
                    family = sys_font.GetFamily() if sys_font.IsOk() else wx.FONTFAMILY_DEFAULT
                    safe = wx.Font(size, family, style, weight, underline)
                    return safe
        except Exception:
            pass
        return font

    def on_set_background_color(self, event):
        """Open custom color picker for background color"""
        dlg = CustomColorDialog(self, "Choose Background Color")
        if hasattr(self, 'editor_background_colour') and self.editor_background_colour:
            dlg.set_color(self.editor_background_colour)
        
        if dlg.ShowModal() == wx.ID_OK:
            color = dlg.get_color()
            self.editor_background_colour = color
            self.apply_editor_appearance()
            self.set_modified()
        dlg.Destroy()

    def on_clear_formatting(self, event):
        """Clear all formatting from selected text"""
        text_ctrl = self.get_text_control()
        if not text_ctrl:
            return
            
        selection_start, selection_end = text_ctrl.GetSelection()
        if selection_start == selection_end:
            # No selection - clear default style
            default_font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            attr = wx.TextAttr()
            attr.SetFont(default_font)
            attr.SetTextColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
            attr.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.SetDefaultStyle(attr)
        else:
            # Clear formatting from selection
            default_font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            attr = wx.TextAttr()
            attr.SetFont(default_font)
            attr.SetTextColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
            attr.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.SetStyle(selection_start, selection_end, attr)
        
        text_ctrl.Refresh()
        self.set_modified()

    def on_toggle_toc_links(self, event):
        """Toggle automatic TOC links in headers"""
        # Store the state on the frame and update preview
        state = self.toc_link_toggle_item.IsChecked()
        setattr(self, "toc_links_enabled", bool(state))
        if self.preview_visible:
            wx.CallAfter(self.update_preview)

    def update_preview(self):
        """Update the preview content"""
        editor = self.get_current_editor()
        content = editor.get_content()

        if MARKDOWN_AVAILABLE:
            try:
                # Set up markdown extensions
                extensions = [
                    'markdown.extensions.tables',
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc',
                    'markdown.extensions.nl2br',
                    'markdown.extensions.sane_lists',
                    'markdown.extensions.smarty',
                ]

                # Add pymdown extensions if available
                if PYMDOWN_AVAILABLE:
                    extensions.extend([
                        'pymdown.extensions.betterem',
                        'pymdown.extensions.superfences',
                        'pymdown.extensions.highlight',
                        'pymdown.extensions.inlinehilite',
                        'pymdown.extensions.magiclink',
                        'pymdown.extensions.tasklist',
                        'pymdown.extensions.tilde',
                        'pymdown.extensions.caret',
                        'pymdown.extensions.mark',
                        'pymdown.extensions.emoji',
                    ])

                # Configure extension settings
                extension_configs = {
                    'markdown.extensions.codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': True,
                    },
                    'markdown.extensions.toc': {
                        'permalink': True,
                    },
                }

                if PYMDOWN_AVAILABLE:
                    extension_configs.update({
                        'pymdown.extensions.highlight': {
                            'css_class': 'highlight',
                            'use_pygments': True,
                        },
                        'pymdown.extensions.superfences': {
                            'custom_fences': []
                        },
                        'pymdown.extensions.tasklist': {
                            'custom_checkbox': True,
                        }
                    })

                # Convert markdown to HTML
                html_content = markdown.markdown(
                    content,
                    extensions=extensions,
                    extension_configs=extension_configs)

                # Enhanced CSS styling with anchor support
                html_page = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        /* GitHub-style markdown rendering */
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
                            font-size: 16px;
                            line-height: 1.5;
                            color: #24292f;
                            background-color: #ffffff;
                            margin: 0;
                            padding: 32px;
                            word-wrap: break-word;
                        }}
                        
                        /* Headers */
                        h1, h2, h3, h4, h5, h6 {{
                            margin-top: 24px;
                            margin-bottom: 16px;
                            font-weight: 600;
                            line-height: 1.25;
                            color: #24292f;
                        }}
                        
                        h1 {{
                            font-size: 2em;
                            border-bottom: 1px solid #d0d7de;
                            padding-bottom: 0.3em;
                        }}
                        
                        h2 {{
                            font-size: 1.5em;
                            border-bottom: 1px solid #d0d7de;
                            padding-bottom: 0.3em;
                        }}
                        
                        h3 {{ font-size: 1.25em; }}
                        h4 {{ font-size: 1em; }}
                        h5 {{ font-size: 0.875em; }}
                        h6 {{ font-size: 0.85em; color: #656d76; }}
                        
                        /* Paragraphs and text */
                        p {{ margin-top: 0; margin-bottom: 16px; }}
                        
                        /* Links */
                        a {{
                            color: #0969da;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                        a:visited {{
                            color: #8250df;
                        }}
                        
                        /* Lists */
                        ul, ol {{
                            margin-top: 0;
                            margin-bottom: 16px;
                            padding-left: 2em;
                        }}
                        
                        li {{ margin-bottom: 0.25em; }}
                        
                        /* Task lists */
                        .task-list-item {{
                            list-style-type: none;
                            margin-left: -1.5em;
                        }}
                        
                        .task-list-item-checkbox {{
                            margin: 0 0.2em 0.25em -1.6em;
                            vertical-align: middle;
                        }}
                        
                        /* Code */
                        code {{
                            padding: 0.2em 0.4em;
                            margin: 0;
                            font-size: 85%;
                            background-color: rgba(175, 184, 193, 0.2);
                            border-radius: 6px;
                            font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
                        }}
                        
                        pre {{
                            padding: 16px;
                            overflow: auto;
                            font-size: 85%;
                            line-height: 1.45;
                            background-color: #f6f8fa;
                            border-radius: 6px;
                            margin-bottom: 16px;
                        }}
                        
                        pre code {{
                            display: inline;
                            max-width: auto;
                            padding: 0;
                            margin: 0;
                            overflow: visible;
                            line-height: inherit;
                            word-wrap: normal;
                            background-color: transparent;
                            border: 0;
                        }}
                        
                        /* Blockquotes */
                        blockquote {{
                            padding: 0 1em;
                            color: #656d76;
                            border-left: 0.25em solid #d0d7de;
                            margin: 0 0 16px 0;
                        }}
                        
                        blockquote > :first-child {{
                            margin-top: 0;
                        }}
                        
                        blockquote > :last-child {{
                            margin-bottom: 0;
                        }}
                        
                        /* Tables */
                        table {{
                            border-spacing: 0;
                            border-collapse: collapse;
                            display: block;
                            width: max-content;
                            max-width: 100%;
                            overflow: auto;
                            margin-bottom: 16px;
                        }}
                        
                        table th {{
                            font-weight: 600;
                            background-color: #f6f8fa;
                        }}
                        
                        table th, table td {{
                            padding: 6px 13px;
                            border: 1px solid #d0d7de;
                        }}
                        
                        table tr {{
                            background-color: #ffffff;
                            border-top: 1px solid #c6cbd1;
                        }}
                        
                        table tr:nth-child(2n) {{
                            background-color: #f6f8fa;
                        }}
                        
                        /* Horizontal rules */
                        hr {{
                            height: 0.25em;
                            padding: 0;
                            margin: 24px 0;
                            background-color: #d0d7de;
                            border: 0;
                        }}
                        
                        /* Strong and emphasis */
                        strong {{ font-weight: 600; }}
                        
                        /* Images */
                        img {{
                            max-width: 100%;
                            box-sizing: content-box;
                        }}
                        
                        /* Syntax highlighting */
                        .highlight {{
                            background: #f6f8fa;
                            border-radius: 6px;
                            padding: 16px;
                            overflow-x: auto;
                        }}
                        
                        /* Table of contents */
                        .toc {{
                            background: #f6f8fa;
                            border: 1px solid #d0d7de;
                            border-radius: 6px;
                            padding: 16px;
                            margin-bottom: 16px;
                        }}
                        
                        .toc ul {{
                            list-style: none;
                            padding-left: 0;
                        }}
                        
                        .toc ul ul {{
                            padding-left: 1em;
                        }}
                        
                        /* Strikethrough */
                        del {{ text-decoration: line-through; }}
                        
                        /* Mark/highlight */
                        mark {{
                            background-color: #fff8c5;
                            padding: 0.1em 0.2em;
                        }}
                        
                        /* Keyboard keys */
                        kbd {{
                            display: inline-block;
                            padding: 3px 5px;
                            font-size: 11px;
                            line-height: 10px;
                            color: #444d56;
                            vertical-align: middle;
                            background-color: #f6f8fa;
                            border: 1px solid #d1d9e0;
                            border-bottom-color: #c6cbd1;
                            border-radius: 6px;
                            box-shadow: inset 0 -1px 0 #c6cbd1;
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                self.preview_html.SetPage(html_page)
            except Exception as e:
                # Fallback to plain text with error info
                escaped_content = content.replace('<',
                                                  '&lt;').replace('>', '&gt;')
                error_msg = str(e).replace('<', '&lt;').replace('>', '&gt;')
                self.preview_html.SetPage(
                    f"<html><body><h3>Markdown Rendering Error:</h3><p>{error_msg}</p><h3>Raw Content:</h3><pre>{escaped_content}</pre></body></html>"
                )
        else:
            # Fallback to plain text if markdown is not available
            escaped_content = content.replace('<', '&lt;').replace('>', '&gt;')
            self.preview_html.SetPage(
                f"<html><body><h3>Markdown Preview (Plain Text)</h3><p><em>Install markdown library for enhanced rendering</em></p><pre>{escaped_content}</pre></body></html>"
            )

    def on_new(self, event):
        """Create a new file"""
        if self.check_save_before_action():
            # Reset both editors to ensure consistency
            self.general_editor.new_file()
            self.structured_editor.new_file()
            self.current_file = None
            self.is_modified = False
            self.update_title()

    def on_open(self, event):
        """Open an existing file"""
        if self.check_save_before_action():
            with wx.FileDialog(
                    self,
                    "Open README file",
                    wildcard=
                    "Markdown files (*.md)|*.md|Text files (*.txt)|*.txt|All files (*.*)|*.*",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return

                pathname = file_dialog.GetPath()
                try:
                    with open(pathname, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Load content into both editors to ensure consistency
                    self.general_editor.load_content(content)
                    self.structured_editor.load_content(content)
                    
                    self.current_file = pathname
                    self.is_modified = False
                    self.update_title()
                    self.status_bar.SetStatusText(
                        f"Opened: {os.path.basename(pathname)}")
                except IOError:
                    wx.LogError(f"Cannot open file '{pathname}'.")

    def on_save(self, event):
        """Save the current file"""
        if self.current_file:
            self.save_file(self.current_file)
        else:
            self.on_save_as(event)

    def on_save_as(self, event):
        """Save the file with a new name"""
        with wx.FileDialog(
                self,
                "Save README file",
                wildcard=
                "Markdown files (*.md)|*.md|Text files (*.txt)|*.txt|All files (*.*)|*.*",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = file_dialog.GetPath()
            self.save_file(pathname)

    def save_file(self, pathname):
        """Save content to file"""
        try:
            content = self.get_current_editor().get_content()
            with open(pathname, 'w', encoding='utf-8') as file:
                file.write(content)
            self.current_file = pathname
            self.is_modified = False
            self.update_title()
            self.status_bar.SetStatusText(
                f"Saved: {os.path.basename(pathname)}")
        except IOError:
            wx.LogError(f"Cannot save file '{pathname}'.")

    def on_exit(self, event):
        """Exit the application"""
        self.Close()

    def on_close(self, event):
        """Handle window close event"""
        if self.check_save_before_action():
            event.Skip()
        else:
            event.Veto()

    def on_about(self, event):
        """Show about dialog"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("README Editor")
        info.SetVersion("1.0")
        info.SetDescription(
            "A comprehensive README editor with general and structured editing capabilities"
        )
        info.SetCopyright("(C) 2024")
        wx.adv.AboutBox(info)

    def on_undo(self, event):
        """Undo last action"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            editor.text_ctrl.Undo()

    def on_redo(self, event):
        """Redo last action"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            editor.text_ctrl.Redo()

    def on_cut(self, event):
        """Cut selected text"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            editor.text_ctrl.Cut()
        elif hasattr(editor, 'section_editor'):
            editor.section_editor.Cut()

    def on_copy(self, event):
        """Copy selected text"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            editor.text_ctrl.Copy()
        elif hasattr(editor, 'section_editor'):
            editor.section_editor.Copy()

    def on_paste(self, event):
        """Paste text from clipboard"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            editor.text_ctrl.Paste()
        elif hasattr(editor, 'section_editor'):
            editor.section_editor.Paste()

    def on_select_all(self, event):
        """Select all text"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            editor.text_ctrl.SelectAll()
        elif hasattr(editor, 'section_editor'):
            editor.section_editor.SelectAll()

    # Format menu handlers
    def get_text_control(self):
        """Get the currently active text control"""
        editor = self.get_current_editor()
        if hasattr(editor, 'text_ctrl'):
            return editor.text_ctrl
        elif hasattr(editor, 'section_editor'):
            return editor.section_editor
        return None

    def insert_text_at_cursor(self, text, select_text=""):
        """Insert text at cursor position, optionally selecting part of it"""
        text_ctrl = self.get_text_control()
        if not text_ctrl:
            return

        # Get current selection
        start_pos = text_ctrl.GetInsertionPoint()
        selection_start, selection_end = text_ctrl.GetSelection()

        if selection_start != selection_end:
            # Replace selected text
            selected_text = text_ctrl.GetStringSelection()
            if select_text:
                # Use selected text as placeholder
                formatted_text = text.replace(select_text, selected_text)
            else:
                formatted_text = text + selected_text
            text_ctrl.Replace(selection_start, selection_end, formatted_text)

            # Position cursor appropriately
            if select_text and selected_text:
                # Don't select anything if we used the selected text
                text_ctrl.SetInsertionPoint(selection_start +
                                            len(formatted_text))
            else:
                # Select the inserted content
                text_ctrl.SetSelection(selection_start,
                                       selection_start + len(formatted_text))
        else:
            # Insert at cursor
            text_ctrl.WriteText(text)

            # Select placeholder text if specified
            if select_text:
                select_start = text.find(select_text)
                if select_start != -1:
                    cursor_pos = start_pos + select_start
                    text_ctrl.SetSelection(cursor_pos,
                                           cursor_pos + len(select_text))

    def insert_header(self, level):
        """Insert a header of the specified level"""
        prefix = "#" * level + " "
        self.insert_text_at_cursor(prefix + "Header Text", "Header Text")

    def on_bold(self, event):
        """Make text bold"""
        self.insert_text_at_cursor("**Bold Text**", "Bold Text")

    def on_italic(self, event):
        """Make text italic"""
        self.insert_text_at_cursor("*Italic Text*", "Italic Text")

    def on_strikethrough(self, event):
        """Apply strikethrough to text"""
        self.insert_text_at_cursor("~~Strikethrough Text~~",
                                   "Strikethrough Text")

    def on_inline_code(self, event):
        """Format text as inline code"""
        self.insert_text_at_cursor("`Code`", "Code")

    def on_code_block(self, event):
        """Insert a code block"""
        code_block = """```python
Your code here
```"""
        self.insert_text_at_cursor(code_block, "Your code here")

    def on_blockquote(self, event):
        """Insert a blockquote"""
        self.insert_text_at_cursor("> Quote text", "Quote text")

    def on_horizontal_rule(self, event):
        """Insert a horizontal rule"""
        text_ctrl = self.get_text_control()
        if text_ctrl:
            cursor_pos = text_ctrl.GetInsertionPoint()
            line_start = text_ctrl.GetLineText(
                text_ctrl.PositionToXY(cursor_pos)[1])

            # Add newlines if not at beginning of empty line
            if line_start.strip():
                rule = "\n\n---\n\n"
            else:
                rule = "---\n\n"

            self.insert_text_at_cursor(rule)

    def on_unordered_list(self, event):
        """Insert an unordered list"""
        list_text = """- List item 1
- List item 2
- List item 3"""
        self.insert_text_at_cursor(list_text, "List item 1")

    def on_ordered_list(self, event):
        """Insert an ordered list"""
        list_text = """1. First item
2. Second item
3. Third item"""
        self.insert_text_at_cursor(list_text, "First item")

    def on_task_list(self, event):
        """Insert a task list"""
        task_text = """- [ ] Task 1
- [ ] Task 2
- [x] Completed task"""
        self.insert_text_at_cursor(task_text, "Task 1")

    def on_link(self, event):
        """Insert a link"""
        # Show dialog to get URL
        dlg = wx.TextEntryDialog(self, "Enter URL:", "Insert Link", "https://")
        if dlg.ShowModal() == wx.ID_OK:
            url = dlg.GetValue()
            link_text = f"[Link Text]({url})"
            self.insert_text_at_cursor(link_text, "Link Text")
        dlg.Destroy()

    def on_image(self, event):
        """Insert an image"""
        # Show dialog to get image URL or path
        dlg = wx.TextEntryDialog(self, "Enter image URL or path:",
                                 "Insert Image", "https://")
        if dlg.ShowModal() == wx.ID_OK:
            url = dlg.GetValue()
            image_text = f"![Alt Text]({url})"
            self.insert_text_at_cursor(image_text, "Alt Text")
        dlg.Destroy()

    def on_table(self, event):
        """Insert a table"""
        table_text = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |"""
        self.insert_text_at_cursor(table_text, "Header 1")

    def check_save_before_action(self):
        """Check if file needs to be saved before performing an action"""
        if self.is_modified:
            dlg = wx.MessageDialog(self, "Do you want to save changes?",
                                   "Unsaved Changes",
                                   wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()

            if result == wx.ID_YES:
                self.on_save(None)
                return not self.is_modified
            elif result == wx.ID_NO:
                return True
            else:
                return False
        return True

    def update_title(self):
        """Update the window title"""
        title = "README Editor"
        
        # Check if we're in structured editing mode and have a project name
        if hasattr(self, 'notebook') and hasattr(self, 'structured_editor'):
            current_page = self.notebook.GetSelection()
            if current_page == 1:  # Structured editor is page 1
                project_name = self.structured_editor.project_name_ctrl.GetValue()
                if project_name and project_name.strip() and project_name != "My Project":
                    title += f" - {project_name.strip()}"
        
        if self.current_file:
            file_name = os.path.basename(self.current_file)
            if " - " not in title:  # If no project name was added
                title += f" - {file_name}"
            else:  # Project name was added, append file name in parentheses
                title += f" ({file_name})"
        
        if self.is_modified:
            title += " *"
        self.SetTitle(title)

    def set_modified(self, modified=True):
        """Set the modified flag"""
        self.is_modified = modified
        self.update_title()


class GeneralEditor(wx.Panel):
    """General purpose README editor"""

    def __init__(self, parent, main_frame=None):
        super().__init__(parent)
        self.main_frame = main_frame
        self.create_ui()

    def create_ui(self):
        """Create the UI for general editor"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Text editor
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_RICH2)
        self.text_ctrl.SetFont(
            wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))

        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        # Bind events
        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_text_changed)

    def apply_appearance(self, font=None, text_colour=None, background_colour=None):
        self._apply_text_control_appearance(self.text_ctrl, font, text_colour, background_colour)

    def _apply_text_control_appearance(self, ctrl, font, text_colour, background_colour):
        """Apply appearance to selected text only, or set default for future typing"""
        try:
            # Get current selection
            selection_start, selection_end = ctrl.GetSelection()
            has_selection = selection_start != selection_end
            
            if has_selection:
                # Apply to selected text using rich text attributes
                attr = wx.TextAttr()
                if font is not None:
                    attr.SetFont(font)
                if text_colour is not None:
                    attr.SetTextColour(text_colour)
                if background_colour is not None:
                    attr.SetBackgroundColour(background_colour)
                
                # Apply style to selection only
                ctrl.SetStyle(selection_start, selection_end, attr)
                
            else:
                # No selection - set default style for future typing
                attr = wx.TextAttr()
                if font is not None:
                    attr.SetFont(font)
                if text_colour is not None:
                    attr.SetTextColour(text_colour)
                if background_colour is not None:
                    attr.SetBackgroundColour(background_colour)
                    
                ctrl.SetDefaultStyle(attr)
                
            # Force refresh to ensure changes are visible
            ctrl.Refresh()
                    
        except Exception as e:
            # Fallback to control-level if rich text fails
            try:
                if font is not None:
                    ctrl.SetFont(font)
                if text_colour is not None:
                    ctrl.SetForegroundColour(text_colour)
                if background_colour is not None:
                    ctrl.SetBackgroundColour(background_colour)
                ctrl.Refresh()
            except:
                pass

    def on_text_changed(self, event):
        """Handle text change event"""
        if self.main_frame:
            self.main_frame.set_modified()
            # Update preview if visible
            if self.main_frame.preview_visible:
                wx.CallAfter(self.main_frame.update_preview)
        event.Skip()

    def new_file(self):
        """Create a new file"""
        self.text_ctrl.SetValue("")

    def load_content(self, content):
        """Load content into the editor"""
        self.text_ctrl.SetValue(content)

    def get_content(self):
        """Get the current content"""
        return self.text_ctrl.GetValue()


class StructuredEditor(wx.Panel):
    """Structured project README editor"""

    def __init__(self, parent, main_frame=None):
        super().__init__(parent)
        self.main_frame = main_frame
        self.template_root = None
        self.item_to_section = {}
        self.current_section = None
        self.create_ui()
        self.setup_template()

    def create_ui(self):
        """Create the UI for structured editor"""
        # Main vertical sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Project name section at the top
        project_panel = wx.Panel(self)
        project_sizer = wx.BoxSizer(wx.HORIZONTAL)

        project_label = wx.StaticText(project_panel, label="Project Name:")
        project_label.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD))

        self.project_name_ctrl = wx.TextCtrl(project_panel, value="My Project")
        self.project_name_ctrl.SetFont(
            wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD))
        self.project_name_ctrl.SetToolTip(
            "Edit your project's main title here. Changes will be reflected in the tree and preview immediately."
        )

        project_sizer.Add(project_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                          5)
        project_sizer.Add(self.project_name_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        project_panel.SetSizer(project_sizer)

        # Project description/overview section
        overview_panel = wx.Panel(self)
        overview_sizer = wx.BoxSizer(wx.VERTICAL)

        overview_label = wx.StaticText(overview_panel, label="Project Description (Overview):")
        overview_label.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD))

        self.overview_ctrl = wx.TextCtrl(overview_panel, 
                                        style=wx.TE_MULTILINE | wx.TE_RICH2,
                                        size=(-1, 80))
        self.overview_ctrl.SetFont(
            wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))
        self.overview_ctrl.SetToolTip(
            "Enter a brief description of your project. This text will appear directly after the project name in the README."
        )

        overview_sizer.Add(overview_label, 0, wx.ALL, 5)
        overview_sizer.Add(self.overview_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        overview_panel.SetSizer(overview_sizer)

        # Create splitter window for the rest
        splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        # Left panel - structure tree with controls
        self.tree_panel = wx.Panel(splitter)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)

        tree_label = wx.StaticText(self.tree_panel, label="README Structure:")

        # Add control buttons
        controls_panel = wx.Panel(self.tree_panel)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.toggle_btn = wx.Button(controls_panel,
                                    label="Toggle Section",
                                    size=(100, -1))
        self.enable_all_btn = wx.Button(controls_panel,
                                        label="Enable All",
                                        size=(80, -1))
        self.disable_all_btn = wx.Button(controls_panel,
                                         label="Disable All",
                                         size=(80, -1))
        self.toggle_optional_btn = wx.Button(controls_panel,
                                            label="Toggle Optional",
                                            size=(100, -1))

        # Automation buttons
        automation_label = wx.StaticText(controls_panel, label="Auto-generate:")
        automation_label.SetFont(
            wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD))

        self.auto_file_structure_btn = wx.Button(controls_panel,
                                               label="File Structure",
                                               size=(100, -1))
        self.auto_file_structure_btn.SetToolTip(
            "Automatically scan the project directory and generate file structure")

        self.auto_dependencies_btn = wx.Button(controls_panel,
                                             label="Dependencies",
                                             size=(100, -1))
        self.auto_dependencies_btn.SetToolTip(
            "Automatically read requirements.txt and populate dependencies section")

        self.auto_dev_deps_btn = wx.Button(controls_panel,
                                         label="Dev Dependencies",
                                         size=(100, -1))
        # New automation buttons
        self.auto_examples_main_btn = wx.Button(controls_panel,
                                               label="Examples → Main",
                                               size=(120, -1))
        self.auto_glossary_btn = wx.Button(controls_panel,
                                          label="Generate Glossary",
                                          size=(140, -1))
        self.auto_dev_deps_btn.SetToolTip(
            "Automatically read requirements-dev.txt and populate developer dependencies section")

        controls_sizer.Add(self.toggle_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.enable_all_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.disable_all_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.toggle_optional_btn, 0, wx.ALL, 2)
        
        # Add automation section
        controls_sizer.Add(wx.StaticLine(controls_panel), 0, wx.EXPAND | wx.ALL, 2)
        controls_sizer.Add(automation_label, 0, wx.ALL, 2)
        controls_sizer.Add(self.auto_file_structure_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.auto_dependencies_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.auto_dev_deps_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.auto_examples_main_btn, 0, wx.ALL, 2)
        controls_sizer.Add(self.auto_glossary_btn, 0, wx.ALL, 2)
        
        controls_panel.SetSizer(controls_sizer)

        self.tree_ctrl = wx.TreeCtrl(self.tree_panel,
                                     style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE)

        tree_sizer.Add(tree_label, 0, wx.ALL, 5)
        tree_sizer.Add(controls_panel, 0, wx.EXPAND | wx.ALL, 5)
        tree_sizer.Add(self.tree_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.tree_panel.SetSizer(tree_sizer)

        # Right panel - content editor
        self.editor_panel = wx.Panel(splitter)
        editor_sizer = wx.BoxSizer(wx.VERTICAL)

        self.current_section_label = wx.StaticText(
            self.editor_panel, label="Select a section to edit")
        self.section_editor = wx.TextCtrl(self.editor_panel,
                                          style=wx.TE_MULTILINE | wx.TE_RICH2)
        self.section_editor.SetFont(
            wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))

        # Add some helpful text initially
        self.section_editor.SetValue(
            "Select a section from the tree on the left to edit its content.\n\nThe tree shows the main H1 sections of your README. Edit the project name in the field above.\n\nThis editor supports the full project README structure with all sections and subsections."
        )

        editor_sizer.Add(self.current_section_label, 0, wx.ALL, 5)
        editor_sizer.Add(self.section_editor, 1, wx.EXPAND | wx.ALL, 5)
        self.editor_panel.SetSizer(editor_sizer)

        # Set up splitter
        splitter.SplitVertically(self.tree_panel, self.editor_panel, 350)
        splitter.SetMinimumPaneSize(200)

        # Add everything to main sizer
        main_sizer.Add(project_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(overview_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        # Bind events
        self.tree_ctrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)
        self.section_editor.Bind(wx.EVT_TEXT, self.on_section_text_changed)
        self.project_name_ctrl.Bind(wx.EVT_TEXT, self.on_project_name_changed)
        self.project_name_ctrl.Bind(wx.EVT_SET_FOCUS,
                                    self.on_project_name_focus)
        self.project_name_ctrl.Bind(wx.EVT_KILL_FOCUS,
                                    self.on_project_name_blur)
        self.overview_ctrl.Bind(wx.EVT_TEXT, self.on_overview_changed)

        # Bind toggle control events
        self.toggle_btn.Bind(wx.EVT_BUTTON, self.on_toggle_section)
        self.enable_all_btn.Bind(wx.EVT_BUTTON, self.on_enable_all_sections)
        self.disable_all_btn.Bind(wx.EVT_BUTTON, self.on_disable_all_sections)
        self.toggle_optional_btn.Bind(wx.EVT_BUTTON, self.on_toggle_optional_sections)
        
        # Bind automation button events
        self.auto_file_structure_btn.Bind(wx.EVT_BUTTON, self.on_auto_generate_file_structure)
        self.auto_dependencies_btn.Bind(wx.EVT_BUTTON, self.on_auto_generate_dependencies)
        self.auto_dev_deps_btn.Bind(wx.EVT_BUTTON, self.on_auto_generate_dev_dependencies)
        self.auto_examples_main_btn.Bind(wx.EVT_BUTTON, self.on_auto_populate_examples_main)
        self.auto_glossary_btn.Bind(wx.EVT_BUTTON, self.on_auto_generate_glossary)

        # Add right-click context menu for tree
        self.tree_ctrl.Bind(wx.EVT_RIGHT_UP, self.on_tree_right_click)

    def apply_appearance(self, font=None, text_colour=None, background_colour=None):
        # Apply to both editors
        self._apply_text_control_appearance(self.section_editor, font, text_colour, background_colour)
        self._apply_text_control_appearance(self.overview_ctrl, font, text_colour, background_colour)

    def _apply_text_control_appearance(self, ctrl, font, text_colour, background_colour):
        """Apply appearance to selected text only, or set default for future typing"""
        try:
            # Get current selection
            selection_start, selection_end = ctrl.GetSelection()
            has_selection = selection_start != selection_end
            
            if has_selection:
                # Apply to selected text using rich text attributes
                attr = wx.TextAttr()
                if font is not None:
                    attr.SetFont(font)
                if text_colour is not None:
                    attr.SetTextColour(text_colour)
                if background_colour is not None:
                    attr.SetBackgroundColour(background_colour)
                
                # Apply style to selection only
                ctrl.SetStyle(selection_start, selection_end, attr)
                
            else:
                # No selection - set default style for future typing
                attr = wx.TextAttr()
                if font is not None:
                    attr.SetFont(font)
                if text_colour is not None:
                    attr.SetTextColour(text_colour)
                if background_colour is not None:
                    attr.SetBackgroundColour(background_colour)
                    
                ctrl.SetDefaultStyle(attr)
                
            # Force refresh to ensure changes are visible
            ctrl.Refresh()
                    
        except Exception as e:
            # Fallback to control-level if rich text fails
            try:
                if font is not None:
                    ctrl.SetFont(font)
                if text_colour is not None:
                    ctrl.SetForegroundColour(text_colour)
                if background_colour is not None:
                    ctrl.SetBackgroundColour(background_colour)
                ctrl.Refresh()
            except:
                pass

    def setup_template(self):
        """Set up the structured README template"""
        self.template_root = create_readme_template()

        # Initialize with current project name
        current_name = self.project_name_ctrl.GetValue() or "My Project"
        self.template_root.name = current_name
        
        # Load any existing overview content
        if self.template_root.content:
            self.overview_ctrl.SetValue(self.template_root.content)

        self.item_to_section = populate_tree_ctrl(self.tree_ctrl,
                                                  self.template_root)

        # Expand first few levels (skip root expansion if hidden)
        root_item = self.tree_ctrl.GetRootItem()
        if root_item.IsOk():
            # Only expand root if it's not hidden
            if not (self.tree_ctrl.GetWindowStyleFlag() & wx.TR_HIDE_ROOT):
                self.tree_ctrl.Expand(root_item)

            # Expand first level children
            child, cookie = self.tree_ctrl.GetFirstChild(root_item)
            while child.IsOk():
                self.tree_ctrl.Expand(child)
                child, cookie = self.tree_ctrl.GetNextChild(root_item, cookie)

    def on_tree_selection(self, event):
        """Handle tree selection change"""
        item = event.GetItem()
        if item.IsOk() and item in self.item_to_section:
            # Save current section content before switching
            if self.current_section is not None:
                self.current_section.content = self.section_editor.GetValue()
                # If we were editing Overview (root content), sync to overview control
                if self.current_section == self.template_root:
                    self.overview_ctrl.SetValue(self.current_section.content)

            # Load new section
            self.current_section = self.item_to_section[item]
            
            # Check if we're selecting the Overview (root content)
            item_text = self.tree_ctrl.GetItemText(item)
            if item_text == "Overview" and self.current_section == self.template_root:
                self.current_section_label.SetLabel("Editing: Overview (Project Description)")
            else:
                self.current_section_label.SetLabel(
                    f"Editing: {self.current_section.get_full_path()}")
            
            self.section_editor.SetValue(self.current_section.content)

            # Update editor state
            self.section_editor.Enable(True)

        event.Skip()

    def on_section_text_changed(self, event):
        """Handle section text change"""
        if self.current_section is not None:
            self.current_section.content = self.section_editor.GetValue()
            
            # If we're editing Overview (root content), sync to overview control
            if self.current_section == self.template_root:
                # Temporarily unbind to avoid recursion
                self.overview_ctrl.Unbind(wx.EVT_TEXT)
                self.overview_ctrl.SetValue(self.current_section.content)
                self.overview_ctrl.Bind(wx.EVT_TEXT, self.on_overview_changed)

        if self.main_frame:
            self.main_frame.set_modified()
            # Update preview if visible
            if self.main_frame.preview_visible:
                wx.CallAfter(self.main_frame.update_preview)
        event.Skip()

    def on_project_name_changed(self, event):
        """Handle project name change"""
        if self.template_root:
            # Update the root section name
            new_name = self.project_name_ctrl.GetValue() or "Project"
            self.template_root.name = new_name

            # Update the tree view to reflect the change
            self.refresh_tree_root()

            # Update status bar to show the change
            if self.main_frame and hasattr(self.main_frame, 'status_bar'):
                self.main_frame.status_bar.SetStatusText(
                    f"Project name updated to: {new_name}")

        if self.main_frame:
            self.main_frame.set_modified()
            # Update the window title to reflect the new project name
            self.main_frame.update_title()
            # Update preview if visible
            if self.main_frame.preview_visible:
                wx.CallAfter(self.main_frame.update_preview)
        event.Skip()

    def on_overview_changed(self, event):
        """Handle overview/description text change"""
        if self.template_root:
            # Store the overview content in the root section
            self.template_root.content = self.overview_ctrl.GetValue()
            
            # If we're currently editing the Overview in the section editor, sync it
            if self.current_section == self.template_root:
                # Temporarily unbind to avoid recursion
                self.section_editor.Unbind(wx.EVT_TEXT)
                self.section_editor.SetValue(self.template_root.content)
                self.section_editor.Bind(wx.EVT_TEXT, self.on_section_text_changed)

        if self.main_frame:
            self.main_frame.set_modified()
            # Update preview if visible
            if self.main_frame.preview_visible:
                wx.CallAfter(self.main_frame.update_preview)
        event.Skip()

    def refresh_tree_root(self):
        """Refresh the tree display to show updated project name"""
        if self.template_root:
            # Store the currently selected section to restore it
            current_selection = None
            current_item = self.tree_ctrl.GetSelection()
            if current_item.IsOk() and current_item in self.item_to_section:
                current_selection = self.item_to_section[current_item]
            
            # Save current section content before refreshing
            if self.current_section is not None:
                self.current_section.content = self.section_editor.GetValue()
            
            # Repopulate the tree with updated project name
            try:
                from .structured_template import populate_tree_ctrl  # type: ignore
            except Exception:
                from structured_template import populate_tree_ctrl  # type: ignore
            self.item_to_section = populate_tree_ctrl(self.tree_ctrl, self.template_root)
            
            # Try to restore the selection
            if current_selection:
                for item, section in self.item_to_section.items():
                    if section == current_selection:
                        self.tree_ctrl.SelectItem(item)
                        break

    def on_project_name_focus(self, event):
        """Handle project name field gaining focus"""
        # Clear any tree selection when editing project name
        # since project name no longer appears in the tree
        self.tree_ctrl.UnselectAll()
        # Clear the section editor to show we're editing the project level
        self.current_section = None
        self.current_section_label.SetLabel(
            "Project Name (edit in field above)")
        self.section_editor.SetValue(
            "The project name is edited in the field above.\n\nThe tree shows the main sections of your README:\n• Overview\n• Table of contents\n• Run Software\n• Project Architecture\n• Usage\n• Example Code\n• Developer Guide\n• References\n• Installation\n• Improvement Plan\n• Contributing\n• License\n• Acknowledgements"
        )
        self.section_editor.Enable(False)
        event.Skip()

    def on_project_name_blur(self, event):
        """Handle project name field losing focus"""
        # Re-enable section editor if there was a selected section
        if self.current_section is None:
            # If no section was selected, enable the editor for general use
            self.section_editor.Enable(True)
            self.current_section_label.SetLabel(
                "Select a section from the tree to edit")
            self.section_editor.SetValue(
                "Select a section from the tree on the left to edit its content.\n\nThe project name is edited in the field above."
            )
        event.Skip()

    def on_toggle_section(self, event):
        """Toggle the enabled/disabled state of the selected section"""
        selection = self.tree_ctrl.GetSelection()
        if selection.IsOk() and selection in self.item_to_section:
            section = self.item_to_section[selection]
            section.enabled = not section.enabled
            self.refresh_tree_display()

            # Update status
            status = "enabled" if section.enabled else "disabled"
            if self.main_frame and hasattr(self.main_frame, 'status_bar'):
                self.main_frame.status_bar.SetStatusText(
                    f"Section '{section.name}' {status}")

            # Mark as modified
            if self.main_frame:
                self.main_frame.set_modified()
                if self.main_frame.preview_visible:
                    wx.CallAfter(self.main_frame.update_preview)

    def on_enable_all_sections(self, event):
        """Enable all sections in the template"""
        if self.template_root:
            self._set_all_sections_enabled(self.template_root, True)
            self.refresh_tree_display()

            if self.main_frame and hasattr(self.main_frame, 'status_bar'):
                self.main_frame.status_bar.SetStatusText(
                    "All sections enabled")

            if self.main_frame:
                self.main_frame.set_modified()
                if self.main_frame.preview_visible:
                    wx.CallAfter(self.main_frame.update_preview)

    def on_disable_all_sections(self, event):
        """Disable all sections in the template (except essential ones)"""
        if self.template_root:
            self._set_all_sections_enabled(self.template_root, False)
            # Keep essential sections enabled
            essential_sections = ["Overview", "Table of contents"]
            self._enable_essential_sections(self.template_root,
                                            essential_sections)
            self.refresh_tree_display()

            if self.main_frame and hasattr(self.main_frame, 'status_bar'):
                self.main_frame.status_bar.SetStatusText(
                    "All sections disabled (except essential ones)")

            if self.main_frame:
                self.main_frame.set_modified()
                if self.main_frame.preview_visible:
                    wx.CallAfter(self.main_frame.update_preview)

    def on_toggle_optional_sections(self, event):
        """Toggle all optional sections in the template"""
        if self.template_root:
            # Check if any optional sections are currently enabled
            any_optional_enabled = self._any_optional_sections_enabled(self.template_root)
            
            # If any are enabled, disable all optional; if none are enabled, enable all optional
            new_state = not any_optional_enabled
            self._set_optional_sections_enabled(self.template_root, new_state)
            self.refresh_tree_display()

            if self.main_frame and hasattr(self.main_frame, 'status_bar'):
                status_text = "All optional sections enabled" if new_state else "All optional sections disabled"
                self.main_frame.status_bar.SetStatusText(status_text)

            if self.main_frame:
                self.main_frame.set_modified()
                if self.main_frame.preview_visible:
                    wx.CallAfter(self.main_frame.update_preview)

    def on_tree_right_click(self, event):
        """Handle right-click on tree for context menu"""
        pt = event.GetPosition()
        item, flags = self.tree_ctrl.HitTest(pt)

        if item.IsOk() and item in self.item_to_section:
            self.tree_ctrl.SelectItem(item)
            section = self.item_to_section[item]

            # Create context menu
            menu = wx.Menu()
            toggle_text = "Disable Section" if section.enabled else "Enable Section"
            menu.Append(1, toggle_text)
            menu.AppendSeparator()
            menu.Append(2, "Enable All Children")
            menu.Append(3, "Disable All Children")

            # Bind menu events
            def on_context_toggle(evt):
                section.enabled = not section.enabled
                self.refresh_tree_display()
                if self.main_frame:
                    self.main_frame.set_modified()
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)

            def on_enable_children(evt):
                self._set_all_sections_enabled(section, True)
                self.refresh_tree_display()
                if self.main_frame:
                    self.main_frame.set_modified()
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)

            def on_disable_children(evt):
                for child in section.children:
                    self._set_all_sections_enabled(child, False)
                self.refresh_tree_display()
                if self.main_frame:
                    self.main_frame.set_modified()
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)

            self.Bind(wx.EVT_MENU, on_context_toggle, id=1)
            self.Bind(wx.EVT_MENU, on_enable_children, id=2)
            self.Bind(wx.EVT_MENU, on_disable_children, id=3)

            # Show menu
            self.PopupMenu(menu)
            menu.Destroy()

    def _set_all_sections_enabled(self, section, enabled):
        """Recursively set enabled state for section and all children"""
        section.enabled = enabled
        for child in section.children:
            self._set_all_sections_enabled(child, enabled)

    def _enable_essential_sections(self, section, essential_names):
        """Enable sections with names in essential_names list"""
        if section.name in essential_names:
            section.enabled = True
        for child in section.children:
            self._enable_essential_sections(child, essential_names)

    def _set_optional_sections_enabled(self, section, enabled):
        """Recursively set enabled state for optional sections only"""
        if section.optional:
            section.enabled = enabled
        for child in section.children:
            self._set_optional_sections_enabled(child, enabled)

    def _any_optional_sections_enabled(self, section):
        """Check if any optional sections are currently enabled"""
        if section.optional and section.enabled:
            return True
        for child in section.children:
            if self._any_optional_sections_enabled(child):
                return True
        return False

    def refresh_tree_display(self):
        """Refresh the tree display to show updated enabled/disabled states"""
        if self.template_root and self.tree_ctrl:
            # Save current selection
            current_selection = self.tree_ctrl.GetSelection()
            current_section = None
            if current_selection.IsOk(
            ) and current_selection in self.item_to_section:
                current_section = self.item_to_section[current_selection]

            # Rebuild tree
            try:
                from .structured_template import populate_tree_ctrl  # type: ignore
            except Exception:
                from structured_template import populate_tree_ctrl  # type: ignore
            self.item_to_section = populate_tree_ctrl(self.tree_ctrl,
                                                      self.template_root)

            # Restore selection if possible
            if current_section:
                for item, section in self.item_to_section.items():
                    if section == current_section:
                        self.tree_ctrl.SelectItem(item)
                        break

    def new_file(self):
        """Create a new structured file"""
        # Reset all sections to empty
        if self.template_root:
            self._clear_all_sections(self.template_root)
            self.section_editor.SetValue("")
            self.current_section_label.SetLabel("Select a section to edit")
            self.current_section = None

        # Reset project name
        self.project_name_ctrl.SetValue("My Project")
        if self.template_root:
            self.template_root.name = "My Project"
            self.refresh_tree_root()

    def _clear_all_sections(self, section):
        """Recursively clear all section content and reset enabled state"""
        section.content = ""
        section.enabled = True  # Reset to enabled state
        for child in section.children:
            self._clear_all_sections(child)

    def load_content(self, content):
        """Load content into the structured editor"""
        # Reset template first
        self.new_file()

        # Try to extract project name from first H1 header
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                project_name = line[2:].strip()
                if project_name:
                    self.project_name_ctrl.SetValue(project_name)
                    if self.template_root:
                        self.template_root.name = project_name
                        # Update the tree view to reflect the loaded project name
                        self.refresh_tree_root()
                break

        # Try to parse markdown content and populate appropriate sections
        self._parse_markdown_content(content)

        # Refresh the current view if a section is selected
        if self.current_section:
            self.section_editor.SetValue(self.current_section.content)

    def _parse_markdown_content(self, content):
        """Parse markdown content and try to match it to template sections"""
        lines = content.split('\n')
        current_section = None
        current_content = []

        # Create a mapping of section names to sections for quick lookup
        section_map = {}
        self._build_section_map(self.template_root, section_map)

        for line in lines:
            # Check if this line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                # Save previous section content
                if current_section and current_content:
                    current_section.content = '\n'.join(
                        current_content).strip()

                # Find matching section
                header_text = header_match.group(2).strip()
                current_section = section_map.get(header_text)
                current_content = []
            else:
                # Add content to current section
                if current_section is not None:
                    current_content.append(line)

        # Save last section
        if current_section and current_content:
            current_section.content = '\n'.join(current_content).strip()

    def _build_section_map(self, section, section_map):
        """Build a mapping of section names to section objects"""
        section_map[section.name] = section
        for child in section.children:
            self._build_section_map(child, section_map)

    def get_content(self):
        """Get the current content as markdown"""
        # Save current editor content to current section
        if self.current_section is not None:
            self.current_section.content = self.section_editor.GetValue()

        # Generate markdown with project name as H1
        if self.template_root:
            project_name = self.project_name_ctrl.GetValue() or "My Project"

            # Start with project name as main H1
            content = f"# {project_name}\n\n"

            # Add any root content if present
            if self.template_root.content:
                content += self.template_root.content + "\n\n"

            # Add all child sections, with special handling for Table of Contents
            for child in self.template_root.children:
                if not child.enabled:
                    continue

                if child.name == "Table of contents":
                    # Auto-generate table of contents
                    auto_toc = self.template_root.generate_table_of_contents()

                    # Create TOC section
                    toc_header = "## Table of contents\n\n"

                    if child.content.strip():
                        # Use custom content and add auto-generated TOC
                        toc_content = toc_header + child.content + "\n\n" + auto_toc + "\n"
                    else:
                        # Use auto-generated TOC only
                        toc_content = toc_header + auto_toc + "\n"

                    content += toc_content + "\n"
                else:
                    # Regular section
                    include_toc_links = bool(getattr(self.main_frame, "toc_links_enabled", False)) if self.main_frame else False
                    child_content = child.to_markdown(include_toc_links=include_toc_links)
                    if child_content.strip():
                        content += child_content + "\n"

            return content.rstrip() + "\n"
        else:
            project_name = self.project_name_ctrl.GetValue() or "My Project"
            return f"# {project_name}\n\nNo content available."

    # Automation methods
    def on_auto_generate_file_structure(self, event):
        """Auto-generate project file structure"""
        try:
            # Get the project directory (where the app is running from or where file is saved)
            if self.main_frame and self.main_frame.current_file:
                project_dir = os.path.dirname(self.main_frame.current_file)
            else:
                project_dir = os.getcwd()
            
            # Generate file structure
            file_structure = self._scan_directory_structure(project_dir)
            
            # Find the "Project Structure" section and populate it
            section = self._find_section_by_name(self.template_root, "Project Structure")
            if section:
                section.content = file_structure
                section.enabled = True
                
                # If this section is currently selected, update the editor
                if self.current_section == section:
                    self.section_editor.SetValue(section.content)
                
                # Refresh tree to show enabled section
                self.refresh_tree_display()
                
                if self.main_frame:
                    self.main_frame.set_modified()
                    if hasattr(self.main_frame, 'status_bar'):
                        self.main_frame.status_bar.SetStatusText(
                            f"Generated file structure for {project_dir}")
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)
            else:
                wx.MessageBox("Could not find 'Project Structure' section in template.",
                            "Section Not Found", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            wx.MessageBox(f"Error generating file structure: {str(e)}",
                        "Error", wx.OK | wx.ICON_ERROR)

    def on_auto_generate_dependencies(self, event):
        """Auto-generate project dependencies from requirements.txt"""
        try:
            # Get the project directory
            if self.main_frame and self.main_frame.current_file:
                project_dir = os.path.dirname(self.main_frame.current_file)
            else:
                project_dir = os.getcwd()
            
            requirements_file = os.path.join(project_dir, "requirements.txt")
            
            if not os.path.exists(requirements_file):
                wx.MessageBox(f"requirements.txt not found in {project_dir}",
                            "File Not Found", wx.OK | wx.ICON_WARNING)
                return
            
            # Read and parse requirements.txt
            dependencies_content = self._parse_requirements_file(requirements_file)
            
            # Find appropriate section(s) for dependencies
            # Prioritize "Dependency" under Project Architecture first
            target_sections = ["Dependency", "Dependencies", "Software Dependencies", "Python Libraries", "Install Dependencies"]
            section = None
            for section_name in target_sections:
                section = self._find_section_by_name(self.template_root, section_name)
                if section:
                    break
            
            if section:
                section.content = dependencies_content
                section.enabled = True
                
                # If this section is currently selected, update the editor
                if self.current_section == section:
                    self.section_editor.SetValue(section.content)
                
                # Refresh tree to show enabled section
                self.refresh_tree_display()
                
                if self.main_frame:
                    self.main_frame.set_modified()
                    if hasattr(self.main_frame, 'status_bar'):
                        self.main_frame.status_bar.SetStatusText(
                            "Generated dependencies from requirements.txt")
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)
            else:
                wx.MessageBox("Could not find a suitable dependencies section in template.",
                            "Section Not Found", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            wx.MessageBox(f"Error generating dependencies: {str(e)}",
                        "Error", wx.OK | wx.ICON_ERROR)

    def on_auto_generate_dev_dependencies(self, event):
        """Auto-generate developer dependencies from requirements-dev.txt"""
        try:
            # Get the project directory
            if self.main_frame and self.main_frame.current_file:
                project_dir = os.path.dirname(self.main_frame.current_file)
            else:
                project_dir = os.getcwd()
            
            dev_requirements_file = os.path.join(project_dir, "requirements-dev.txt")
            
            if not os.path.exists(dev_requirements_file):
                wx.MessageBox(f"requirements-dev.txt not found in {project_dir}",
                            "File Not Found", wx.OK | wx.ICON_WARNING)
                return
            
            # Read and parse requirements-dev.txt
            dev_dependencies_content = self._parse_requirements_file(dev_requirements_file, is_dev=True)
            
            # Find appropriate section(s) for developer dependencies
            target_sections = ["Install Developer Tools", "Developer Dependencies", "Development Setup", "Dev Dependencies"]
            section = None
            for section_name in target_sections:
                section = self._find_section_by_name(self.template_root, section_name)
                if section:
                    break
            
            if section:
                section.content = dev_dependencies_content
                section.enabled = True
                
                # If this section is currently selected, update the editor
                if self.current_section == section:
                    self.section_editor.SetValue(section.content)
                
                # Refresh tree to show enabled section
                self.refresh_tree_display()
                
                if self.main_frame:
                    self.main_frame.set_modified()
                    if hasattr(self.main_frame, 'status_bar'):
                        self.main_frame.status_bar.SetStatusText(
                            "Generated developer dependencies from requirements-dev.txt")
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)
            else:
                wx.MessageBox("Could not find a suitable developer dependencies section in template.",
                            "Section Not Found", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            wx.MessageBox(f"Error generating developer dependencies: {str(e)}",
                        "Error", wx.OK | wx.ICON_ERROR)

    def on_auto_populate_examples_main(self, event):
        """Populate Example Code > Main from examples/ directory"""
        try:
            # Resolve project root
            project_dir = os.path.dirname(self.main_frame.current_file) if (self.main_frame and self.main_frame.current_file) else os.getcwd()
            examples_dir = os.path.join(project_dir, "examples")
            if not os.path.isdir(examples_dir):
                wx.MessageBox(f"examples/ directory not found in {project_dir}", "Not Found", wx.OK | wx.ICON_WARNING)
                return
            # Concatenate example files into a markdown code block listing
            combined = []
            for root_dir, _, files in os.walk(examples_dir):
                for fn in sorted(files):
                    file_path = os.path.join(root_dir, fn)
                    rel = os.path.relpath(file_path, project_dir)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                    except Exception:
                        code = ""
                    combined.append(f"### {rel}\n\n```\n{code}\n```\n")
            content_md = "\n".join(combined).strip() or "No examples found."
            # Find Example Code > Main
            section = self._find_section_by_name(self.template_root, "Main")
            if section:
                section.content = content_md
                section.enabled = True
                if self.current_section == section:
                    self.section_editor.SetValue(section.content)
                self.refresh_tree_display()
                if self.main_frame:
                    self.main_frame.set_modified()
                    if hasattr(self.main_frame, 'status_bar'):
                        self.main_frame.status_bar.SetStatusText("Populated Example Code → Main from examples/")
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)
            else:
                wx.MessageBox("Could not find 'Main' under Example Code.", "Section Not Found", wx.OK | wx.ICON_WARNING)
        except Exception as e:
            wx.MessageBox(f"Error populating examples: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def on_auto_generate_glossary(self, event):
        """Generate Glossary terms by scanning codebase for docstrings and identifiers"""
        try:
            project_dir = os.path.dirname(self.main_frame.current_file) if (self.main_frame and self.main_frame.current_file) else os.getcwd()
            terms = self._scan_glossary_terms(project_dir)
            if not terms:
                wx.MessageBox("No glossary terms found.", "Info", wx.OK | wx.ICON_INFORMATION)
                return
            lines = ["### Glossary\n"]
            for term, definition in sorted(terms.items()):
                lines.append(f"- **{term}**: {definition}")
            glossary_md = "\n".join(lines)
            # Find References > Glossary
            glossary_section = self._find_section_by_name(self.template_root, "Glossary")
            if glossary_section:
                glossary_section.content = glossary_md
                glossary_section.enabled = True
                if self.current_section == glossary_section:
                    self.section_editor.SetValue(glossary_section.content)
                self.refresh_tree_display()
                if self.main_frame:
                    self.main_frame.set_modified()
                    if hasattr(self.main_frame, 'status_bar'):
                        self.main_frame.status_bar.SetStatusText("Generated glossary from codebase")
                    if self.main_frame.preview_visible:
                        wx.CallAfter(self.main_frame.update_preview)
            else:
                wx.MessageBox("Could not find 'Glossary' section.", "Section Not Found", wx.OK | wx.ICON_WARNING)
        except Exception as e:
            wx.MessageBox(f"Error generating glossary: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def _scan_glossary_terms(self, project_dir: str):
        """Scan Python files for function/class names and first docstring line as definition"""
        terms = {}
        try:
            import ast
        except Exception:
            return terms
        for root_dir, _, files in os.walk(project_dir):
            # Skip virtual envs and common dirs
            base = os.path.basename(root_dir)
            if base in {'.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules', '.pytest_cache', 'dist', 'build'}:
                continue
            for fn in files:
                if fn.endswith('.py'):
                    file_path = os.path.join(root_dir, fn)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            source = f.read()
                        tree = ast.parse(source, filename=file_path)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                name = node.name
                                doc = ast.get_docstring(node) or ""
                                first = doc.strip().splitlines()[0] if doc.strip() else "Definition not available."
                                if name not in terms:
                                    terms[name] = first
                    except Exception:
                        continue
        return terms

    # Helper methods for automation
    def _find_section_by_name(self, section, name):
        """Recursively find a section by name"""
        if section.name == name:
            return section
        for child in section.children:
            result = self._find_section_by_name(child, name)
            if result:
                return result
        return None

    def _scan_directory_structure(self, directory):
        """Scan directory and generate markdown file structure"""
        try:
            def generate_tree(path, prefix="", is_last=True, max_depth=3, current_depth=0):
                if current_depth > max_depth:
                    return ""
                
                items = []
                try:
                    for item in sorted(os.listdir(path)):
                        # Skip hidden files and common unwanted directories
                        if item.startswith('.') or item in ['__pycache__', 'node_modules', '.git', '.venv', 'venv', 'env', '.pytest_cache']:
                            continue
                        items.append(item)
                except PermissionError:
                    return f"{prefix}├── [Permission Denied]\n"
                
                result = ""
                for i, item in enumerate(items):
                    is_last_item = i == len(items) - 1
                    item_path = os.path.join(path, item)
                    
                    if is_last_item:
                        result += f"{prefix}└── {item}\n"
                        new_prefix = prefix + "    "
                    else:
                        result += f"{prefix}├── {item}\n"
                        new_prefix = prefix + "│   "
                    
                    if os.path.isdir(item_path) and current_depth < max_depth:
                        result += generate_tree(item_path, new_prefix, is_last_item, max_depth, current_depth + 1)
                
                return result
            
            project_name = os.path.basename(directory)
            tree_content = f"```\n{project_name}/\n"
            tree_content += generate_tree(directory, "", True)
            tree_content += "```\n\n"
            tree_content += f"Generated from: `{directory}`"
            
            return tree_content
            
        except Exception as e:
            return f"Error generating file structure: {str(e)}"

    def _parse_requirements_file(self, requirements_file, is_dev=False):
        """Parse requirements.txt file and generate markdown content"""
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            content = ""
            if is_dev:
                content += "### Development Dependencies\n\n"
                content += "These packages are required for development and testing:\n\n"
            else:
                content += "### Required Dependencies\n\n"
                content += "This project requires the following Python packages:\n\n"
            
            # Parse requirements
            packages = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Handle different requirement formats
                    if '>=' in line:
                        package, version = line.split('>=', 1)
                        packages.append(f"- **{package.strip()}** >= {version.strip()}")
                    elif '==' in line:
                        package, version = line.split('==', 1)
                        packages.append(f"- **{package.strip()}** (version {version.strip()})")
                    elif '>' in line:
                        package, version = line.split('>', 1)
                        packages.append(f"- **{package.strip()}** > {version.strip()}")
                    elif '<' in line:
                        package, version = line.split('<', 1)
                        packages.append(f"- **{package.strip()}** < {version.strip()}")
                    else:
                        packages.append(f"- **{line.strip()}**")
            
            if packages:
                content += "\n".join(packages)
                content += "\n\n"
                if is_dev:
                    content += "#### Install Development Dependencies\n\n"
                    content += "```bash\n"
                    content += "pip install -r requirements-dev.txt\n"
                    content += "```"
                else:
                    content += "#### Install Dependencies\n\n"
                    content += "```bash\n"
                    content += "pip install -r requirements.txt\n"
                    content += "```"
            else:
                content += "No dependencies found in requirements file."
            
            return content
            
        except Exception as e:
            return f"Error reading requirements file: {str(e)}"


if __name__ == "__main__":
    app = ReadmeEditorApp()
    app.MainLoop()
