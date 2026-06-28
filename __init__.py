import bpy
from bpy.props import (
    StringProperty,
    CollectionProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
    AddonPreferences,
)

# ------------------------------------------------------------------------
#    Properties
# ------------------------------------------------------------------------

class THEMEPANEL_PG_pinned_item(PropertyGroup):
    """Stores a pinned theme data path"""
    data_path: StringProperty(name="Data Path")

class THEMEPANEL_PG_theme_group_item(PropertyGroup):
    """Stores a data path belonging to a theme group"""
    data_path: StringProperty(name="Data Path")

def resolve_path(root, path):
    """Resolves data paths containing indices like 'bone_color_sets[0].normal'"""
    parts = path.split(".")
    obj = root
    for p in parts[:-1]:
        if "[" in p and p.endswith("]"):
            name, idx_str = p.split("[")
            idx = int(idx_str[:-1])
            obj = getattr(obj, name)[idx]
        else:
            obj = getattr(obj, p)
    return obj, parts[-1]

def update_group_color(self, context):
    """Callback when a theme group's color changes"""
    theme = context.preferences.themes[0]
    for item in self.items:
        try:
            # Resolve the path dynamically
            obj, prop_name = resolve_path(theme, item.data_path)
            
            # The value could be a FloatVector (color)
            val = getattr(obj, prop_name)
            # If length matches, copy
            if len(self.color) == len(val):
                setattr(obj, prop_name, self.color)
            else:
                # E.g., setting a 3-float color to a 4-float theme color
                new_val = list(self.color)
                if len(val) == 4 and len(new_val) == 3:
                    new_val.append(val[3]) # Keep alpha
                elif len(val) == 3 and len(new_val) == 4:
                    new_val = new_val[:3]
                setattr(obj, prop_name, new_val)
        except Exception as e:
            print(f"ThemePanel: Failed to update {item.data_path}: {e}")

def update_global_roundness(self, context):
    theme = context.preferences.themes[0]
    val = self.global_roundness
    if hasattr(theme.user_interface, 'panel_roundness'):
        theme.user_interface.panel_roundness = val
    for attr in dir(theme.user_interface):
        if attr.startswith('wcol_'):
            wcol = getattr(theme.user_interface, attr)
            if hasattr(wcol, 'roundness'):
                wcol.roundness = val

def update_global_shadetop(self, context):
    theme = context.preferences.themes[0]
    val = int(self.global_shadetop)
    for attr in dir(theme.user_interface):
        if attr.startswith('wcol_'):
            wcol = getattr(theme.user_interface, attr)
            if hasattr(wcol, 'shadetop'):
                wcol.shadetop = val

def update_global_shadedown(self, context):
    theme = context.preferences.themes[0]
    val = int(self.global_shadedown)
    for attr in dir(theme.user_interface):
        if attr.startswith('wcol_'):
            wcol = getattr(theme.user_interface, attr)
            if hasattr(wcol, 'shadedown'):
                wcol.shadedown = val

def update_global_show_shaded(self, context):
    theme = context.preferences.themes[0]
    val = self.global_show_shaded
    for attr in dir(theme.user_interface):
        if attr.startswith('wcol_'):
            wcol = getattr(theme.user_interface, attr)
            if hasattr(wcol, 'show_shaded'):
                wcol.show_shaded = val

class THEMEPANEL_PG_theme_group(PropertyGroup):
    """A group of theme colors that share the same color"""
    name: StringProperty(name="Group Name", default="New Group")
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        update=update_group_color
    )
    items: CollectionProperty(type=THEMEPANEL_PG_theme_group_item)

def get_theme_enum_items(self, context):
    import os
    import bpy
    items = []
    
    addon_dir = os.path.dirname(__file__)
    
    # Add installed themes
    paths = bpy.utils.preset_paths("interface_theme")
    has_blender_dark = False
    for p in paths:
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f.endswith(".xml"):
                    filepath = os.path.join(p, f)
                    if f.lower() == "blender_dark.xml":
                        has_blender_dark = True
                    # Don't duplicate if the same filename is already added (e.g. system vs user presets)
                    existing_filenames = [os.path.basename(i[0]) for i in items]
                    if f not in existing_filenames:
                        items.append((filepath, f[:-4].replace("_", " ").title(), filepath))
                        
    # If Blender Dark wasn't found in the presets folders, add our bundled Default.xml / default.xml as "Blender Dark"
    if not has_blender_dark:
        default_xml = os.path.join(addon_dir, "default.xml")
        if not os.path.exists(default_xml):
            default_xml = os.path.join(addon_dir, "Default.xml")
        if os.path.exists(default_xml):
            items.insert(0, (default_xml, "Blender Dark", default_xml))
                        
    if not items:
        items.append(("", "No Themes Found", ""))
        
    return items

class THEMEPANEL_AddonPreferences(AddonPreferences):
    bl_idname = __name__

    pinned_items: CollectionProperty(type=THEMEPANEL_PG_pinned_item)
    theme_groups: CollectionProperty(type=THEMEPANEL_PG_theme_group)
    
    theme_source: bpy.props.EnumProperty(
        name="Source Theme",
        description="Select the theme XML to base the auto-grouping on",
        items=get_theme_enum_items,
    )
    
    color_threshold: FloatProperty(
        name="Color Match Threshold",
        description="Threshold distance for grouping similar colors (0.0 means exact match only)",
        default=0.01,
        min=0.0,
        max=1.0,
    )
    
    global_roundness: FloatProperty(
        name="Global Roundness",
        description="Apply roundness to all widgets",
        default=0.4,
        min=0.0,
        max=1.0,
        update=update_global_roundness
    )
    
    global_shadetop: IntProperty(
        name="Global Shading Top",
        description="Apply top shading to all widgets",
        default=0,
        min=-100,
        max=100,
        update=update_global_shadetop
    )
    
    global_shadedown: IntProperty(
        name="Global Shading Down",
        description="Apply bottom shading to all widgets",
        default=0,
        min=-100,
        max=100,
        update=update_global_shadedown
    )
    
    global_show_shaded: bpy.props.BoolProperty(
        name="Global Show Shaded",
        description="Enable shading for all widgets",
        default=False,
        update=update_global_show_shaded
    )
    
    show_pinned_section: bpy.props.BoolProperty(name="Pinned Elements", default=True)
    show_global_section: bpy.props.BoolProperty(name="Global Settings", default=True)
    show_theme_section: bpy.props.BoolProperty(name="Theme Edit", default=True)
    
    panel_location: bpy.props.EnumProperty(
        name="Panel Location",
        description="Choose where the Theme Panel is displayed",
        items=[
            ('HEADER', "Top Bar Header", "Display as a popover button in the top header"),
            ('N_PANEL', "N-Panel (Sidebar)", "Display as a tab in the 3D Viewport sidebar"),
        ],
        default='HEADER',
        update=lambda self, context: setattr(context.window_manager, "keyconfigs", context.window_manager.keyconfigs) # Triggers redraw/update of UI
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Theme Panel Settings (Pinned Items & Groups are stored here).")
        layout.label(text=f"Pinned Items: {len(self.pinned_items)}")
        layout.label(text=f"Theme Groups: {len(self.theme_groups)}")
        
        row = layout.row()
        row.prop(self, "panel_location")
        
        row = layout.row()
        row.prop(self, "color_threshold")
        
        row = layout.row()
        row.operator("themepanel.clear_all", text="Clear All Data")


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class THEMEPANEL_OT_clear_all(Operator):
    """Clear all pinned items and theme groups"""
    bl_idname = "themepanel.clear_all"
    bl_label = "Clear Theme Panel Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        prefs.pinned_items.clear()
        prefs.theme_groups.clear()
        return {'FINISHED'}

class THEMEPANEL_OT_pin_property(Operator):
    """Pin property to Theme Panel"""
    bl_idname = "themepanel.pin_property"
    bl_label = "Pin to Theme Panel"
    
    # We will grab the data path from the context when right-clicking

    @classmethod
    def poll(cls, context):
        # Only show in themes section
        return hasattr(context, "button_pointer")

    def execute(self, context):
        if not hasattr(context, "button_pointer") or not hasattr(context, "button_prop"):
            self.report({'WARNING'}, "Cannot pin this property.")
            return {'CANCELLED'}
        
        ptr = context.button_pointer
        prop = context.button_prop
        
        # We need to construct the full data path relative to themes[0]
        # Since path_from_id() fails for some theme types, we search recursively.
        # We also pass the target property identifier so we can verify the match:
        # a pointer match is only valid if the property actually exists on that object.
        def find_property_path(current_obj, target_ptr, prop_id, current_path=""):
            if current_obj.as_pointer() == target_ptr.as_pointer():
                # Verify the property actually exists here
                if prop_id in current_obj.bl_rna.properties:
                    return current_path
                # Otherwise keep searching deeper — the real owner is a child
                
            for p in current_obj.bl_rna.properties:
                if p.identifier == 'rna_type': continue
                if p.type == 'POINTER':
                    child = getattr(current_obj, p.identifier)
                    if child:
                        new_path = f"{current_path}.{p.identifier}" if current_path else p.identifier
                        res = find_property_path(child, target_ptr, prop_id, new_path)
                        if res is not None:
                            return res
                elif p.type == 'COLLECTION':
                    coll = getattr(current_obj, p.identifier)
                    try:
                        for idx, child in enumerate(coll):
                            if child and hasattr(child, "as_pointer"):
                                new_path = f"{current_path}.{p.identifier}[{idx}]" if current_path else f"{p.identifier}[{idx}]"
                                res = find_property_path(child, target_ptr, prop_id, new_path)
                                if res is not None:
                                    return res
                    except Exception as e:
                        pass
            return None
            
        theme = context.preferences.themes[0]
        rel_path = find_property_path(theme, ptr, prop.identifier)
        
        if rel_path is not None:
            final_path = f"{rel_path}.{prop.identifier}" if rel_path else prop.identifier
            
            prefs = context.preferences.addons[__name__].preferences
            
            # Check if already pinned
            for p in prefs.pinned_items:
                if p.data_path == final_path:
                    self.report({'INFO'}, "Property already pinned.")
                    return {'CANCELLED'}
            
            new_pin = prefs.pinned_items.add()
            new_pin.data_path = final_path
            self.report({'INFO'}, f"Pinned: {final_path}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Can only pin Theme properties.")
            return {'CANCELLED'}

def draw_context_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(THEMEPANEL_OT_pin_property.bl_idname, icon='PINNED')


# ------------------------------------------------------------------------
#    Auto-Group Logic
# ------------------------------------------------------------------------

import os
import xml.etree.ElementTree as ET

def get_rna_paths_from_xml(element, path=''):
    paths = []
    tag = element.tag
    if tag not in ['bpy', 'Theme']:
        if not tag.startswith('Theme'):
            path = f"{path}.{tag}" if path else tag
            
    for attr, val in element.attrib.items():
        if val.startswith('#') and len(val) in (7, 9):
            paths.append((f"{path}.{attr}" if path else attr, val))
            
    for child in element:
        paths.extend(get_rna_paths_from_xml(child, path))
        
    return paths

class THEMEPANEL_OT_auto_group(Operator):
    """Group theme properties by identical colors based on selected theme XML"""
    bl_idname = "themepanel.auto_group"
    bl_label = "Auto-Group Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        xml_path = prefs.theme_source
        
        # If the selected XML is Blender Dark (the default theme), it usually contains 
        # very few override values since it inherits from hardcoded defaults.
        # Redirect it to our bundled default.xml / Default.xml to parse the complete colors.
        if xml_path and os.path.basename(xml_path).lower() == "blender_dark.xml":
            addon_dir = os.path.dirname(__file__)
            fallback_xml = os.path.join(addon_dir, "default.xml")
            if not os.path.exists(fallback_xml):
                fallback_xml = os.path.join(addon_dir, "Default.xml")
            if os.path.exists(fallback_xml):
                xml_path = fallback_xml
        
        if not xml_path or not os.path.exists(xml_path):
            self.report({'WARNING'}, "Selected XML not found.")
            return {'CANCELLED'}
            
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse XML: {e}")
            return {'CANCELLED'}
            
        all_paths = get_rna_paths_from_xml(root)
        
        prefs.theme_groups.clear()
        
        def hex_to_rgba(h):
            h = h.lstrip('#')
            if len(h) == 6:
                return (int(h[0:2], 16)/255.0, int(h[2:4], 16)/255.0, int(h[4:6], 16)/255.0, 1.0)
            elif len(h) == 8:
                return (int(h[0:2], 16)/255.0, int(h[2:4], 16)/255.0, int(h[4:6], 16)/255.0, int(h[6:8], 16)/255.0)
            return (0.0, 0.0, 0.0, 1.0)
            
        def color_distance(c1, c2):
            return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2 + (c1[3]-c2[3])**2)**0.5

        # Semantic names mapping
        SEMANTIC_NAMES = {
            "#4772b3ff": "Accent / Selection",
            "#4772b3": "Accent / Selection",
            "#ffffff": "Primary Highlights",
            "#e6e6e6": "Primary Text",
            "#eeeeee": "Headers",
            "#3d3d3dff": "Panel Backgrounds & Outlines",
            "#545454ff": "Widget Backgrounds",
            "#000000": "Shadows & Wires",
            "#1d1d1dff": "Deep Backgrounds",
            "#242424ff": "Deep Backgrounds",
            "#303030b3": "Transparent Backgrounds",
            "#333333": "Checker Primary",
            "#262626": "Checker Secondary",
            "#f5f14d": "Gizmo Primary",
            "#63ffff": "Gizmo Secondary",
        }

        # Group by color using threshold
        clusters = [] # list of dicts: {'center': rgba, 'paths': [], 'hex': color_str}
        
        for path, color_str in all_paths:
            rgba = hex_to_rgba(color_str)
            added_to_cluster = False
            for cluster in clusters:
                if color_distance(cluster['center'], rgba) <= prefs.color_threshold:
                    cluster['paths'].append(path)
                    added_to_cluster = True
                    break
            if not added_to_cluster:
                clusters.append({'center': rgba, 'paths': [path], 'hex': color_str.lower()})

        # Create groups in properties
        group_idx = 1
        clusters.sort(key=lambda x: len(x['paths']), reverse=True)
        
        for cluster in clusters:
            if len(cluster['paths']) > 1: # Only group if more than 1 item shares the color
                new_group = prefs.theme_groups.add()
                r, g, b, a = cluster['center']
                
                # Check for semantic name, otherwise fallback to generic
                sem_name = SEMANTIC_NAMES.get(cluster['hex'])
                if sem_name:
                    name = sem_name
                else:
                    hex_str = "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
                    name = f"Group {group_idx} ({hex_str})"
                    
                new_group.name = name
                new_group.color = cluster['center']
                for p in cluster['paths']:
                    item = new_group.items.add()
                    item.data_path = p
                group_idx += 1
                
        # Force update theme colors
        for group in prefs.theme_groups:
            update_group_color(group, context)
                
        xml_name = os.path.basename(xml_path)
        self.report({'INFO'}, f"Created {len(prefs.theme_groups)} groups from {xml_name} and updated theme.")
        return {'FINISHED'}


# ------------------------------------------------------------------------
#    UI Panels & Theme Load/Save
# ------------------------------------------------------------------------
from bpy_extras.io_utils import ImportHelper

class THEMEPANEL_OT_load_theme(Operator, ImportHelper):
    """Load a theme XML file"""
    bl_idname = "themepanel.load_theme"
    bl_label = "Load Theme"
    
    filename_ext = ".xml"
    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be truncated.
    )

    def execute(self, context):
        bpy.ops.preferences.theme_install(filepath=self.filepath)
        self.report({'INFO'}, f"Loaded Theme: {self.filepath}")
        return {'FINISHED'}

class THEMEPANEL_OT_unpin_property(Operator):
    """Unpin property from Theme Panel"""
    bl_idname = "themepanel.unpin"
    bl_label = "Unpin"
    
    data_path: StringProperty()
    
    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        for i, item in enumerate(prefs.pinned_items):
            if item.data_path == self.data_path:
                prefs.pinned_items.remove(i)
                break
        return {'FINISHED'}

class THEMEPANEL_OT_save_theme(Operator):
    """Save the current theme as a preset (goes to AppData)"""
    bl_idname = "themepanel.save_theme"
    bl_label = "Save Theme"
    
    def execute(self, context):
        bpy.ops.wm.interface_theme_preset_add('INVOKE_DEFAULT')
        return {'FINISHED'}

class THEMEPANEL_OT_apply_theme(Operator):
    """Apply the selected theme XML directly to Blender"""
    bl_idname = "themepanel.apply_theme"
    bl_label = "Apply Theme"
    
    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        xml_path = prefs.theme_source
        import os
        if xml_path and os.path.exists(xml_path):
            try:
                # Use execute_preset to apply the theme in-memory.
                # This prevents copying the file to the user presets directory (no duplicate files).
                bpy.ops.script.execute_preset(
                    filepath=xml_path,
                    menu_idname="USERPREF_MT_interface_theme_presets"
                )
                self.report({'INFO'}, f"Applied Theme: {os.path.basename(xml_path)}")
                return {'FINISHED'}
            except Exception as e:
                self.report({'ERROR'}, f"Failed to apply theme: {e}")
                return {'CANCELLED'}
        self.report({'WARNING'}, "Invalid theme selected.")
        return {'CANCELLED'}

class THEMEPANEL_OT_reset_font(Operator):
    """Reset the UI or Monospaced font path to default"""
    bl_idname = "themepanel.reset_font"
    bl_label = "Reset Font"
    bl_options = {'REGISTER', 'UNDO'}
    
    font_type: StringProperty()
    
    def execute(self, context):
        view_prefs = context.preferences.view
        if self.font_type == 'UI':
            view_prefs.font_path_ui = ""
            self.report({'INFO'}, "Reset UI Font to default")
        elif self.font_type == 'MONO':
            view_prefs.font_path_mono = ""
            self.report({'INFO'}, "Reset Mono Font to default")
        return {'FINISHED'}

class THEMEPANEL_OT_add_pin_from_clipboard(Operator):
    """Pin a property by reading its data path from the clipboard"""
    bl_idname = "themepanel.add_pin_from_clipboard"
    bl_label = "Pin from Clipboard"
    
    def execute(self, context):
        clipboard = context.window_manager.clipboard
        if not clipboard:
            self.report({'WARNING'}, "Clipboard is empty.")
            return {'CANCELLED'}
            
        theme = context.preferences.themes[0]
        try:
            obj, prop_name = resolve_path(theme, clipboard)
            
            # Check if property exists
            if prop_name in obj.bl_rna.properties:
                prefs = context.preferences.addons[__name__].preferences
                for p in prefs.pinned_items:
                    if p.data_path == clipboard:
                        self.report({'INFO'}, "Property already pinned.")
                        return {'CANCELLED'}
                new_pin = prefs.pinned_items.add()
                new_pin.data_path = clipboard
                self.report({'INFO'}, f"Pinned: {clipboard}")
                return {'FINISHED'}
        except Exception as e:
            pass
            
        self.report({'WARNING'}, f"Clipboard does not contain a valid theme data path: {clipboard}")
        return {'CANCELLED'}
# UI Panels & Layout Classes
        
class THEMEPANEL_PT_popover(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Theme Panel"
    bl_ui_units_x = 15

    def draw(self, context):
        THEMEPANEL_PT_popover.draw_shared(self, context)

    @staticmethod
    def draw_shared(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__].preferences
        theme = context.preferences.themes[0]
        

        
        # Pinned Section
        box = layout.box()
        row = box.row()
        icon = 'TRIA_DOWN' if prefs.show_pinned_section else 'TRIA_RIGHT'
        row.prop(prefs, "show_pinned_section", text="", icon=icon, emboss=False)
        row.label(text="Pinned Elements", icon='PINNED')
        row.operator("themepanel.add_pin_from_clipboard", text="", icon='PASTEDOWN')
        
        if prefs.show_pinned_section:
            if not prefs.pinned_items:
                box.label(text="No pinned items. Right-click theme properties to pin.")
            else:
                for item in prefs.pinned_items:
                    try:
                        obj, prop_name = resolve_path(theme, item.data_path)
                        rna_prop = obj.bl_rna.properties.get(prop_name)
                        
                        if rna_prop is None:
                            row = box.row(align=True)
                            row.label(text=f"Not found: {item.data_path}", icon='ERROR')
                            op = row.operator("themepanel.unpin", text="", icon='X')
                            op.data_path = item.data_path
                            continue
                        
                        if rna_prop.type == 'POINTER':
                            sub_struct = getattr(obj, prop_name)
                            struct_box = box.box()
                            
                            row = struct_box.row(align=True)
                            row.label(text=prop_name.replace("_", " ").title(), icon='SYSTEM')
                            op = row.operator("themepanel.unpin", text="", icon='X')
                            op.data_path = item.data_path
                            
                            for sub_prop in sub_struct.bl_rna.properties:
                                if sub_prop.identifier == 'rna_type':
                                    continue
                                if sub_prop.type == 'ENUM':
                                    struct_box.prop_menu_enum(sub_struct, sub_prop.identifier)
                                else:
                                    struct_box.prop(sub_struct, sub_prop.identifier)
                        
                        elif rna_prop.type == 'ENUM':
                            row = box.row(align=True)
                            split = row.split(factor=0.85)
                            split.prop_menu_enum(obj, prop_name)
                            op = split.operator("themepanel.unpin", text="", icon='X')
                            op.data_path = item.data_path
                        
                        else:
                            row = box.row(align=True)
                            split = row.split(factor=0.85)
                            
                            prop_row = split.row()
                            prop_row.prop(obj, prop_name)
                            
                            op_row = split.row()
                            op = op_row.operator("themepanel.unpin", text="", icon='X')
                            op.data_path = item.data_path
                            
                    except Exception as e:
                        row = box.row(align=True)
                        row.label(text=f"Error: {item.data_path}")
                        op = row.operator("themepanel.unpin", text="", icon='X')
                        op.data_path = item.data_path
                        
        # Global Settings Section
        layout.separator()
        box = layout.box()
        row = box.row()
        icon = 'TRIA_DOWN' if prefs.show_global_section else 'TRIA_RIGHT'
        row.prop(prefs, "show_global_section", text="", icon=icon, emboss=False)
        row.label(text="Global Settings", icon='MODIFIER')
        
        if prefs.show_global_section:
            col = box.column(align=True)
            col.prop(prefs, "global_roundness", text="Roundness")
            col.prop(prefs, "global_show_shaded", text="Show Shaded")
            col.prop(prefs, "global_shadetop", text="Shading Top")
            col.prop(prefs, "global_shadedown", text="Shading Down")
            
            # Expose global fonts from view preferences with reset buttons
            col.separator()
            col.label(text="Interface Fonts", icon='FONT_DATA')
            view_prefs = context.preferences.view
            
            row = col.row(align=True)
            row.prop(view_prefs, "font_path_ui", text="UI")
            op = row.operator("themepanel.reset_font", text="", icon='LOOP_BACK')
            op.font_type = 'UI'
            
            row = col.row(align=True)
            row.prop(view_prefs, "font_path_mono", text="Mono")
            op = row.operator("themepanel.reset_font", text="", icon='LOOP_BACK')
            op.font_type = 'MONO'
        
        # Theme Edit Section
        layout.separator()
        box = layout.box()
        row = box.row()
        icon = 'TRIA_DOWN' if prefs.show_theme_section else 'TRIA_RIGHT'
        row.prop(prefs, "show_theme_section", text="", icon=icon, emboss=False)
        row.label(text="Theme Edit", icon='COLOR')
        
        if prefs.show_theme_section:
            row = box.row()
            row.prop(prefs, "theme_source", text="")
            row.operator("themepanel.apply_theme", text="", icon='IMPORT')
            
            row = box.row(align=True)
            row.prop(prefs, "color_threshold", text="Threshold")
            row.operator("themepanel.auto_group", text="Auto-Group", icon='FILE_REFRESH')
            
            row = box.row(align=True)
            row.operator("themepanel.load_theme", text="Load Theme", icon='FILE_FOLDER')
            row.operator("themepanel.save_theme", text="Save Theme", icon='FILE_TICK')
            
            if not prefs.theme_groups:
                box.label(text="No groups. Click auto-group.")
            else:
                for group in prefs.theme_groups:
                    row = box.row()
                    row.prop(group, "name", text="")
                    row.prop(group, "color", text="")


class THEMEPANEL_PT_sidebar(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Theme'
    bl_label = "Theme Panel"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[__name__].preferences
        return prefs.panel_location == 'N_PANEL'

    def draw(self, context):
        THEMEPANEL_PT_popover.draw_shared(self, context)


def draw_header_button(self, context):
    prefs = context.preferences.addons[__name__].preferences
    if prefs.panel_location == 'HEADER':
        layout = self.layout
        layout.popover(THEMEPANEL_PT_popover.__name__, text="", icon='COLOR')

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    THEMEPANEL_PG_pinned_item,
    THEMEPANEL_PG_theme_group_item,
    THEMEPANEL_PG_theme_group,
    THEMEPANEL_AddonPreferences,
    THEMEPANEL_OT_clear_all,
    THEMEPANEL_OT_pin_property,
    THEMEPANEL_OT_unpin_property,
    THEMEPANEL_OT_add_pin_from_clipboard,
    THEMEPANEL_OT_auto_group,
    THEMEPANEL_OT_load_theme,
    THEMEPANEL_OT_save_theme,
    THEMEPANEL_OT_apply_theme,
    THEMEPANEL_OT_reset_font,
    THEMEPANEL_PT_popover,
    THEMEPANEL_PT_sidebar,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.VIEW3D_HT_header.append(draw_header_button)
    bpy.types.WM_MT_button_context.append(draw_context_menu)

def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_header_button)
    bpy.types.WM_MT_button_context.remove(draw_context_menu)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
