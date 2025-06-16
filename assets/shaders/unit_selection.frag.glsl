#version 330 core

// Fragment shader for pulsing dotted effect
out vec4 fragColor;
uniform float p3d_Time;          // built-in time uniform
uniform vec4 indicatorColor;     // RGBA color of the circle
uniform float pulseSpeed;        // speed of the pulsing effect
uniform float dashFrequency;     // how many dashes per full circle

void main() {
    // Compute angle around the circle based on fragment's normalized coordinates
    float angle = atan(gl_FragCoord.y - 0.5, gl_FragCoord.x - 0.5);
    float normalizedAngle = (angle + 3.14159265) / (2.0 * 3.14159265);

    // Pulsing dash: use sine wave to modulate alpha at a given frequency and speed
    float dash = step(0.5, fract(normalizedAngle * dashFrequency - p3d_Time * pulseSpeed));
    float alpha = dash * indicatorColor.a;

    // Output final color with pulsing alpha
    fragColor = vec4(indicatorColor.rgb, alpha);
}
