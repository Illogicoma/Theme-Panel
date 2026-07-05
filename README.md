The **Theme Panel** is a compact tool designed to streamline your workflow through two primary features:

### 1. Pinning Preference Elements

You can right-click any element in `Preferences -> Themes` and pin it directly to the Theme Panel, allowing you to edit it on the fly.

> **Why?** > When modeling in general, I prefer working with large vertices. However, when doing terrain work with hundreds of millions of verts, I need smaller ones. Opening the preferences menu to change the vertex size every single time was highly suboptimal. Theme Panel solves this!

### 2. Rapid Theme Editing & Auto-Grouping

You can load and save themes directly within the Theme Panel. Additionally, the **Auto-Group** command enables rapid, sweeping theme adjustments.

> **Why?** > You want to try some things but editing a theme sometimes require finding and changing 15 identical color values individually. The Auto-Group function solves this by combining color and alpha values into a single parameter based on a set threshold. This allows you to edit all highlighted, dark, or light elements simultaneously.

---

### UI

By default, the **Theme Panel** is added to the top bar (near the viewport shading settings), but it can be set in preferences to live in the **N-panel** instead.

Security Notice: Loading Custom Themes

This add-on allows you to load and parse external .xml theme files. To ensure a safe and secure experience, please keep the following guidelines in mind:



⚠️ Security Notice: Loading Custom Themes

This add-on allows you to load and parse external .xml theme files. To ensure a safe and secure experience, please keep the following guidelines in mind:

Source Trust: Only import theme XML files from sources you know and trust (such as official repositories, reputable creators, or themes you have exported yourself).

Safe File Format: Theme files are stored in XML format, which is a standard markup language containing color values and layout configurations. Unlike Python scripts (.py), XML files do not contain executable code and cannot run scripts on your computer.

Blender Native Mechanics: Loading and applying XML themes within this panel utilizes Blender's native preset parsing engine. The security profile is identical to using Blender's built-in Preferences > Themes > Install... option.

Inspectable Data: If you are ever unsure about a downloaded theme, you can open any .xml file in a standard text editor (like Notepad or VS Code) to inspect its content before loading it. It should only consist of nested XML tags containing color hex codes and numeric values.
