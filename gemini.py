bl_info = {
    "name": "Gemini Playground",
    "blender": (3, 6, 0),
    "category": "Development",
}

import bpy
import time
from typing import List, Tuple, Optional
import google.generativeai as genai
from bpy.props import StringProperty, PointerProperty, EnumProperty
from PIL import Image

class GP_OT_RunGeminiPlayground(bpy.types.Operator):
    bl_idname = "gp.run_gemini_playground"
    bl_label = "Run Gemini Playground"

    def execute(self, context):
        properties = context.scene.gp_properties

        # Check if Google API key is provided
        if not properties.google_api_key:
            self.report({'ERROR'}, 'Google API key is not set.')
            return {'CANCELLED'}

        # Set up Google Generative AI
        genai.configure(api_key=properties.google_api_key)
        generation_config = genai.types.GenerationConfig(
            temperature=properties.temperature,
            max_output_tokens=properties.max_output_tokens,
            stop_sequences=self.preprocess_stop_sequences(properties.stop_sequences),
            top_k=properties.top_k,
            top_p=properties.top_p
        )

        # Generate content based on text or image prompt
        if properties.model_type == 'GEMINI_PRO':
            model = genai.GenerativeModel('gemini-pro')
            prompt = properties.text_prompt
        elif properties.model_type == 'GEMINI_PRO_VISION':
            model = genai.GenerativeModel('gemini-pro-vision')
            if properties.image_path:  # Check if image path is provided
                image_prompt = Image.open(properties.image_path)
                prompt = [properties.vision_text_prompt, image_prompt]
            else:
                prompt = properties.vision_text_prompt

        response = model.generate_content(prompt, stream=True, generation_config=generation_config)
        response.resolve()

        # Display the output result
        properties.output_result = response.text

        return {'FINISHED'}

    def preprocess_stop_sequences(self, stop_sequences):
        if not stop_sequences:
            return None
        return [sequence.strip() for sequence in stop_sequences.split(",")]

class GP_OT_CopyResultText(bpy.types.Operator):
    bl_idname = "gp.copy_result_text"
    bl_label = "Copy Result Text"

    def execute(self, context):
        properties = context.scene.gp_properties
        bpy.context.window_manager.clipboard = properties.output_result
        self.report({'INFO'}, 'Result text copied to clipboard!')
        return {'FINISHED'}

class GP_Properties(bpy.types.PropertyGroup):
    google_api_key: StringProperty(name="Google API Key", description="Provide your own GOOGLE API KEY")
    text_prompt: StringProperty(name="Text Prompt", default="Hi there!")
    image_path: StringProperty(name="Image Path", default="", subtype='FILE_PATH')  # Store the image path as a string
    output_result: StringProperty(name="Output Result", default="", subtype='FILE_PATH')
    temperature: bpy.props.FloatProperty(name="Temperature", default=0.4, min=0, max=1)
    max_output_tokens: bpy.props.IntProperty(name="Max Output Tokens", default=1024, min=1)
    stop_sequences: bpy.props.StringProperty(name="Stop Sequences", default="")
    top_k: bpy.props.IntProperty(name="Top-K", default=32, min=1, max=40)
    top_p: bpy.props.FloatProperty(name="Top-P", default=1, min=0, max=1)
    model_type: bpy.props.EnumProperty(
        name="Model Type",
        items=[
            ('GEMINI_PRO', 'Gemini Pro', 'Generate content based on text prompt'),
            ('GEMINI_PRO_VISION', 'Gemini Pro Vision', 'Generate content based on text prompt and vision'),
        ],
        default='GEMINI_PRO',
    )
    vision_text_prompt: StringProperty(name="Vision Text Prompt", default="Describe the image")

class GP_PT_GeminiPlaygroundPanel(bpy.types.Panel):
    bl_idname = "PT_GeminiPlaygroundPanel"
    bl_label = "Gemini Playground"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        properties = context.scene.gp_properties

        layout.prop(properties, "google_api_key")
        layout.prop(properties, "model_type")  # Add model type dropdown

        if properties.model_type == 'GEMINI_PRO':
            layout.prop(properties, "text_prompt")
        elif properties.model_type == 'GEMINI_PRO_VISION':
            layout.prop(properties, "vision_text_prompt", text="Vision Text Prompt")  # Vision text prompt
            layout.prop(properties, "image_path", text="Image Path")  # Use image path for Vision model

        layout.operator("gp.run_gemini_playground")

        # Display the result text in multiple lines (13 words per line)
        box = layout.box()
        box.label(text="Result of Gemini Playground:")
        words = properties.output_result.split()
        lines = [' '.join(words[i:i+13]) for i in range(0, len(words), 13)]
        for line in lines:
            box.label(text=line)

        layout.prop(properties, "temperature")
        layout.prop(properties, "max_output_tokens")
        layout.prop(properties, "stop_sequences")
        layout.prop(properties, "top_k")
        layout.prop(properties, "top_p")

        # Add the copy button
        layout.operator("gp.copy_result_text")

def register():
    bpy.utils.register_class(GP_OT_RunGeminiPlayground)
    bpy.utils.register_class(GP_OT_CopyResultText)
    bpy.utils.register_class(GP_Properties)
    bpy.utils.register_class(GP_PT_GeminiPlaygroundPanel)
    bpy.types.Scene.gp_properties = bpy.props.PointerProperty(type=GP_Properties)

def unregister():
    bpy.utils.unregister_class(GP_OT_RunGeminiPlayground)
    bpy.utils.unregister_class(GP_OT_CopyResultText)
    bpy.utils.unregister_class(GP_Properties)
    bpy.utils.unregister_class(GP_PT_GeminiPlaygroundPanel)
    del bpy.types.Scene.gp_properties

if __name__ == "__main__":
    register()
