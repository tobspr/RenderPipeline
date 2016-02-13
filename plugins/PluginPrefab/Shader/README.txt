Put your shaders into this directory. 
You should put include files right into this directory, and stage shaders
into the Stage/ directory.

--

You can access regular shader files with self.get_shader_resource("shader_name.glsl")

-- 

You can access stage shader files (Stored in Stages/) inside of a RenderStage with:

self.load_plugin_shader("<StageName>.frag.glsl")

