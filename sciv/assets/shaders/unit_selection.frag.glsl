#version 330 core

in vec2 v_uv;           
out vec4 fragColor;     

uniform float time;        
uniform float dashFreq;    
uniform float pulseSpeed;  
uniform float borderWidth; 
uniform vec4 color;        

const float PI = 3.141592653589793;

void main() {
    float d = length(v_uv);
    float R = 1.0 - borderWidth;
    float r = R - borderWidth;
    float edge = smoothstep(r - 0.005, r + 0.005, d)
               - smoothstep(R - 0.005, R + 0.005, d);

    float ang = atan(v_uv.y, v_uv.x);
    float normAng = (ang + PI) / (2.0 * PI);

    float dash = step(0.5, fract(normAng * dashFreq - time * pulseSpeed));

    fragColor = vec4(color.rgb, edge * dash * color.a);
}
