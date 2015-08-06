#version 410 compatibility

#extension GL_ARB_separate_shader_objects : enable

// Input from the vertex shader
//tobspr's old include. we'll use the struct below.
//#include "Includes/VertexOutput.include"
//layout(location=0) in VertexOutput vOutput;

struct VertexTerrainOutput {
    vec3 positionWorld;
    vec3 normalWorld;
    vec2 texcoord;
    vec4 lastProjectedPos;
    //float fogFactor;
    vec2 texUVrepeat;
    };
    
layout(location=0) in VertexTerrainOutput vOutput;

// This is required for the materials and must come after vOutput's definition
#pragma include "Includes/MaterialPacking.include"

uniform sampler2D p3d_Texture0;//color maps....
uniform sampler2D p3d_Texture1;  
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;
uniform sampler2D p3d_Texture4;
uniform sampler2D p3d_Texture5;
uniform sampler2D p3d_Texture6;//normal maps...
uniform sampler2D p3d_Texture7;
uniform sampler2D p3d_Texture8;
uniform sampler2D p3d_Texture9;
uniform sampler2D p3d_Texture10;
uniform sampler2D p3d_Texture11;

uniform sampler2D atr1; // rgb values are for mapping details
uniform sampler2D atr2; // rgb values are for mapping details

uniform sampler2D height; // a heightmap
//uniform sampler2D walkmap; // walkmap

//uniform vec4 fog; //fog color + for adjust in alpha
uniform vec4 ambient; //ambient light color

// Also this enables us to compute the tangent in
// the fragment shader
//#include "Includes/TangentFromDDX.include"

uniform float osg_FrameTime;

void main() {
    
    //if(vOutput.fogFactor>0.996) //fog only version
    //    {
        //gl_FragData[0] = fog;            
        //gl_FragData[1] = vec4(1.0,0.0,0.0,0.0);
        // Create a material to store the properties on
    //    Material m;
    //    m.baseColor = fog.xyz;
    //    m.roughness = 0.5;
    //    m.specular = 0.5;
    //    m.metallic = 0.0;
    //    m.normal = vec3(1.0,0.0,0.0);
    //    m.position = vOutput.positionWorld.xyz;
    //    m.translucency = 0.0;
    //    renderMaterial(m);
    //    }
    //else //full version
    //    {
        vec3 norm=vec3(0.0,0.0,1.0);    
        const vec3 vLeft=vec3(1.0,0.0,0.0); 
        float gloss = 1.0;        
        const float pixel = 1.0/512.0;
        const vec3 off = vec3(-pixel, 0, pixel);
        const float height_scale=100.0;
        
        //normal vector...
        //vec4 me=texture2D(height,vOutput.texcoord);
        //vec4 n=texture2D(height, vec2(vOutput.texcoord.x,vOutput.texcoord.y+pixel)); 
        //vec4 s=texture2D(height, vec2(vOutput.texcoord.x,vOutput.texcoord.y-pixel));   
        //vec4 e=texture2D(height, vec2(vOutput.texcoord.x+pixel,vOutput.texcoord.y));    
        //vec4 w=texture2D(height, vec2(vOutput.texcoord.x-pixel,vOutput.texcoord.y));
        
        float me = texture2D(height,vOutput.texcoord).x;
        float w = texture2D(height, vec2(vOutput.texcoord.xy + off.xy)).x;
        float e = texture2D(height, vec2(vOutput.texcoord.xy + off.zy)).x;
        float s = texture2D(height, vec2(vOutput.texcoord.xy + off.yx)).x;
        float n = texture2D(height, vec2(vOutput.texcoord.xy + off.yz)).x;

        //find perpendicular vector to norm:        
        vec3 temp = norm; //a temporary vector that is not parallel to norm    
        temp.x+=0.5;
        //form a basis with norm being one of the axes:
        vec3 perp1 = normalize(cross(norm,temp));
        vec3 perp2 = normalize(cross(norm,perp1));
        //use the basis to move the normal in its own space by the offset
        vec3 normalOffset = -height_scale*(( (n-me) - (s-me))*perp1 - ((e-me) - (w-me))*perp2);
        
        //norm += normalOffset;  
        //norm = normalize(gl_NormalMatrix * norm);
        norm = normalize(vOutput.normalWorld + normalOffset);
        
        //TBN
        //vec3 tangent=  gl_NormalMatrix * cross(norm, vLeft);  
        //vec3 binormal= gl_NormalMatrix * cross(norm, tangent);  
        vec3 tangent = cross(norm, vLeft);
        vec3 binormal = cross(norm, tangent);
        
        //mix the textures
        vec4 mask1=texture2D(atr1,vOutput.texcoord);
        vec4 mask2=texture2D(atr2,vOutput.texcoord);
        //detail
        vec4 tex0 = texture2D(p3d_Texture0, vOutput.texUVrepeat);
        vec4 tex1 = texture2D(p3d_Texture1, vOutput.texUVrepeat);
        vec4 tex2 = texture2D(p3d_Texture2, vOutput.texUVrepeat);
        vec4 tex3 = texture2D(p3d_Texture3, vOutput.texUVrepeat);
        vec4 tex4 = texture2D(p3d_Texture4, vOutput.texUVrepeat);
        vec4 tex5 = texture2D(p3d_Texture5, vOutput.texUVrepeat);
        
        vec4 detail = vec4(0.0,0.0,0.0,0.0);
        detail+=tex0*mask1.r;
        detail+=tex1*mask1.g;
        detail+=tex2*mask1.b;
        detail+=tex3*mask2.r;
        detail+=tex4*mask2.g;
        detail+=tex5*mask2.b;
        //normal
        vec4 tex0n = texture2D(p3d_Texture6, vOutput.texUVrepeat);
        vec4 tex1n = texture2D(p3d_Texture7, vOutput.texUVrepeat);
        vec4 tex2n = texture2D(p3d_Texture8, vOutput.texUVrepeat);
        vec4 tex3n = texture2D(p3d_Texture9, vOutput.texUVrepeat);
        vec4 tex4n = texture2D(p3d_Texture10, vOutput.texUVrepeat);
        vec4 tex5n = texture2D(p3d_Texture11, vOutput.texUVrepeat);
        
        vec4 norm_gloss = vec4(0.0,0.0,0.0,0.0);
        norm_gloss+=tex0n*mask1.r;
        norm_gloss+=tex1n*mask1.g;
        norm_gloss+=tex2n*mask1.b;
        norm_gloss+=tex3n*mask2.r;
        norm_gloss+=tex4n*mask2.g;
        norm_gloss+=tex5n*mask2.b;        
        gloss*=norm_gloss.a;
        norm_gloss=norm_gloss*2.0-1.0;
        norm.xyz *= norm_gloss.z;
        norm.xyz += tangent * norm_gloss.x;
        norm.xyz += binormal * norm_gloss.y;    
        //tobspr's mixedNormal
        norm = normalize(norm);
        
        //lights   
        //vec4 color = ambient;    
        //vec3 lightDir, halfV;
        //float NdotL, NdotHV; 
        //lightDir = normalize(gl_LightSource[0].position.xyz); 
        //halfV= normalize(gl_LightSource[0].halfVector.xyz);    
        //NdotL = max(dot(norm,lightDir),0.0);
        //if (NdotL > 0.0)
        //   {
        //   NdotHV = max(dot(norm,halfV),0.0);
        //   color += gl_LightSource[0].diffuse * NdotL;        
        //   color +=pow(NdotHV,100.0*gloss)*gloss*2.0;
        //   } 
        //vec4 final= vec4(color.rgb * detail.xyz, 1.0);
        
        //m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
        //m.baseColor = mix(final, fog, fogFactor);

        Material m;
        //m.baseColor = final.xyz;
        m.baseColor = detail.xyz;
        m.roughness = 0.7;
        m.specular = 0.2; //gloss;
        m.metallic = 0.0;
        m.normal = norm;
        m.position = vOutput.positionWorld.xyz;
        m.translucency = 0.0;
        renderMaterial(m);
        
        //gl_FragData[0] = mix(final, fog, vOutput.fogFactor);
        //gl_FragData[1]=vec4(vOutput.fogFactor, 0.0,0.0,0.0);
        
    //    }
    }
    