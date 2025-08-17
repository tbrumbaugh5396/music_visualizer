#!/usr/bin/env python3
"""
Create macOS Application Icon for Music Visualizer
Generates a high-resolution icon with an audio waveform and spectrum design
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math


def create_icon():
    """Create a modern icon for Music Visualizer"""

    # Create high-resolution image for icon (1024x1024 for macOS)
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background with rounded corners and modern gradient
    margin = 80
    bg_rect = [margin, margin, size - margin, size - margin]

    # Draw rounded rectangle background with dark music-themed color
    corner_radius = 120
    # Dark gradient from purple-blue to deep blue
    draw.rounded_rectangle(bg_rect, corner_radius,
                           fill=(24, 31, 56, 255))  # Deep dark blue

    # Add subtle border with audio-themed accent
    border_margin = margin - 10
    border_rect = [
        border_margin, border_margin, size - border_margin,
        size - border_margin
    ]
    draw.rounded_rectangle(border_rect,
                           corner_radius + 10,
                           outline=(102, 204, 255, 120),  # Cyan accent
                           width=8)

    # Draw audio spectrum analyzer bars
    center_x = size // 2
    center_y = size // 2
    
    # Spectrum bars configuration
    num_bars = 24
    bar_width = 20
    max_height = 300
    spacing = 8
    total_width = num_bars * bar_width + (num_bars - 1) * spacing
    start_x = center_x - total_width // 2

    # Create spectrum bars with varying heights
    bar_heights = []
    for i in range(num_bars):
        # Create a realistic spectrum curve (higher in middle, lower on sides)
        normalized_pos = abs(i - num_bars / 2) / (num_bars / 2)
        base_height = max_height * (0.3 + 0.7 * (1 - normalized_pos * 0.8))
        # Add some variation
        variation = 0.2 + 0.8 * (math.sin(i * 0.8) * 0.5 + 0.5)
        final_height = base_height * variation
        bar_heights.append(final_height)

    # Draw spectrum bars with gradient colors
    for i, height in enumerate(bar_heights):
        x = start_x + i * (bar_width + spacing)
        y_top = center_y - height // 2
        y_bottom = center_y + height // 2
        
        # Color gradient from cyan to magenta based on height
        height_ratio = height / max_height
        if height_ratio > 0.7:
            color = (255, 64, 255, 255)  # Magenta for high frequencies
        elif height_ratio > 0.4:
            color = (64, 255, 255, 255)  # Cyan for mid frequencies  
        else:
            color = (64, 255, 128, 255)  # Green for low frequencies
            
        # Draw bar with rounded corners
        draw.rounded_rectangle([x, y_top, x + bar_width, y_bottom], 
                              bar_width // 4, fill=color)
        
        # Add glow effect
        glow_margin = 3
        glow_color = (*color[:3], 60)  # Same color but transparent
        draw.rounded_rectangle([x - glow_margin, y_top - glow_margin, 
                               x + bar_width + glow_margin, y_bottom + glow_margin], 
                              bar_width // 3, outline=glow_color, width=2)

    # Draw waveform in the bottom section
    wave_y = center_y + 200
    wave_width = 600
    wave_start_x = center_x - wave_width // 2
    wave_end_x = center_x + wave_width // 2
    
    # Generate smooth waveform points
    wave_points = []
    num_points = 200
    for i in range(num_points):
        x = wave_start_x + (wave_width * i) / (num_points - 1)
        # Create a complex waveform with multiple frequencies
        t = i / num_points * 8 * math.pi
        amplitude = 40 * (math.sin(t) * 0.5 + math.sin(t * 2.3) * 0.3 + math.sin(t * 0.7) * 0.2)
        y = wave_y + amplitude
        wave_points.append((x, y))
    
    # Draw waveform with thick line
    for i in range(len(wave_points) - 1):
        draw.line([wave_points[i], wave_points[i + 1]], 
                 fill=(255, 255, 255, 200), width=6)
    
    # Add a subtle reflection of the waveform
    reflection_points = []
    for x, y in wave_points:
        reflected_y = wave_y + (wave_y - y) * 0.3  # Flip and scale down
        reflection_points.append((x, reflected_y))
    
    for i in range(len(reflection_points) - 1):
        draw.line([reflection_points[i], reflection_points[i + 1]], 
                 fill=(255, 255, 255, 80), width=4)

    # Add a music note symbol in the top area
    note_x = center_x
    note_y = center_y - 280
    note_size = 60
    
    # Draw a stylized music note
    # Note head (circle)
    draw.ellipse([note_x - note_size//3, note_y - note_size//4, 
                  note_x + note_size//3, note_y + note_size//4], 
                 fill=(255, 255, 255, 255))
    
    # Note stem (draw from top to bottom, so y0 < y1)
    stem_x = note_x + note_size//3 - 8
    stem_top = note_y - note_size*2
    stem_bottom = note_y - note_size//4
    draw.rectangle([stem_x, stem_top, stem_x + 8, stem_bottom], 
                   fill=(255, 255, 255, 255))
    
    # Note flag
    flag_points = [
        (stem_x + 8, note_y - note_size*2),
        (stem_x + 40, note_y - note_size*1.5),
        (stem_x + 35, note_y - note_size*1.2),
        (stem_x + 8, note_y - note_size*1.4)
    ]
    draw.polygon(flag_points, fill=(255, 255, 255, 255))

    return img


def create_icon_set():
    """Create a complete icon set for macOS"""

    base_icon = create_icon()

    # Icon sizes for macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Create icons directory
    if not os.path.exists("icons"):
        os.makedirs("icons")

    for size in sizes:
        # Resize image with high quality
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)

        # Save as PNG
        filename = f"icons/music_visualizer_{size}x{size}.png"
        resized.save(filename, "PNG")
        print(f"Created {filename}")

    # Save the main icon
    base_icon.save("icons/music_visualizer.png", "PNG")
    print("Created icons/music_visualizer.png")

    # Create ICO file for cross-platform compatibility
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128),
                 (256, 256)]
    ico_images = []

    for size in ico_sizes:
        resized = base_icon.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized)

    # Save as ICO
    ico_images[0].save("icons/music_visualizer.ico", format="ICO", sizes=ico_sizes)
    print("Created icons/music_visualizer.ico")

    print("\n🎵 Music Visualizer icon set created successfully!")
    print("📱 For macOS app bundle, use the PNG files.")
    print("🖥️  For cross-platform compatibility, use the ICO file.")
    print("🎨 Icon features: audio spectrum bars, waveform, and music note")
    print("\nIcon files created:")
    print("  • icons/music_visualizer.png (main icon)")
    print("  • icons/music_visualizer.ico (Windows compatible)")
    print("  • icons/music_visualizer_*.png (various sizes for macOS)")


if __name__ == "__main__":
    create_icon_set()
