#version 330

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

in vec4 i_pos_scale;
in vec4 i_uv0;
in vec4 i_uv1;
in vec4 i_uv2;
in vec4 i_uv3;
in vec4 i_uv4;
in vec4 i_uv5;
in vec4 i_uv6;

uniform mat4 p3d_ModelViewProjectionMatrix;

out vec2 v_base_uv;
out vec4 v_pos_scale;
out vec4 v_uv0;
out vec4 v_uv1;
out vec4 v_uv2;
out vec4 v_uv3;
out vec4 v_uv4;
out vec4 v_uv5;
out vec4 v_uv6;
out vec2 v_local;

void main() {
    v_base_uv = p3d_MultiTexCoord0;
    v_pos_scale = i_pos_scale;

    v_uv0 = i_uv0;
    v_uv1 = i_uv1;
    v_uv2 = i_uv2;
    v_uv3 = i_uv3;
    v_uv4 = i_uv4;
    v_uv5 = i_uv5;
    v_uv6 = i_uv6;

    vec3 local = vec3(p3d_Vertex.x * i_pos_scale.w, p3d_Vertex.z * i_pos_scale.w, 0.0);
    v_local = local.xy;

    vec3 world = local + i_pos_scale.xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(world, 1.0);
}
