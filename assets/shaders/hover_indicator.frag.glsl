#version 330 core

in vec2 v_uv;              
out vec4 fragColor;

uniform float time;        
uniform float dashFreq;    
uniform float pulseSpeed; 
uniform float borderWidth; 
uniform vec4  color;       

const float PI = 3.141592653589793;

void main() {
    float dist   = length(v_uv);
    float inner  = 1.0 - borderWidth - 0.025;
    float outer  = 1.0 + borderWidth - 0.035;
    float ringM  = step(inner, dist) * step(dist, outer);

    float ang  = atan(v_uv.y, v_uv.x);
    float u    = (ang + PI) / (2.0 * PI);
    float seg  = fract(u * dashFreq);
    float dashM = step(0.1, seg) * step(seg, 0.9);

    float smoothPulse = 0.5 + 0.5 * cos(time * pulseSpeed);

    float pulse = step(0.5, smoothPulse);

    float alpha = ringM * dashM * pulse;

    fragColor = vec4(color.rgb, alpha);
}
