#version 330 core

in vec4  p3d_Vertex;   
in vec3  a_tangent;    
in float a_s;          
in float a_side;       
in float a_v;         

uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ProjectionMatrix;

uniform vec3  u_world_up;     
uniform float u_width_world;  
uniform float u_cap_boost;    
uniform float u_cap_ramp;     

out float v_v;

void main() {
    vec3 t = normalize(a_tangent);
    vec3 up = normalize(u_world_up);
    vec3 side = cross(up, t);
    float L = length(side);
    if (L < 1e-6) {
        vec3 ref = (abs(t.z) < 0.9) ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
        side = cross(ref, t);
        L = length(side);
        if (L < 1e-6) side = vec3(0.0, 1.0, 0.0);
    }
    side /= L;

    float edgeS = min(a_s, 1.0 - a_s) / max(u_cap_ramp, 1e-6);
    float widen = 1.0 + u_cap_boost * clamp(1.0 - edgeS, 0.0, 1.0);

    vec3 pos_world = p3d_Vertex.xyz + side * (u_width_world * widen * a_side);
    vec4 pos_view  = p3d_ModelViewMatrix * vec4(pos_world, 1.0);
    gl_Position    = p3d_ProjectionMatrix * pos_view;

    v_v = a_v;
}