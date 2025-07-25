from PIL import Image, ImageDraw
import os

def create_syswatch_icon():
    # Create a 64x64 icon
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle - blue
    draw.ellipse([2, 2, size-2, size-2], fill=(37, 99, 235, 255), outline=(30, 64, 175, 255), width=2)
    
    # Monitor/screen - white background
    monitor_x, monitor_y = 18, 20
    monitor_w, monitor_h = 28, 18
    draw.rectangle([monitor_x, monitor_y, monitor_x + monitor_w, monitor_y + monitor_h], 
                   fill=(255, 255, 255, 255), outline=(229, 231, 235, 255), width=1)
    
    # Screen - dark
    screen_x, screen_y = 20, 22
    screen_w, screen_h = 24, 14
    draw.rectangle([screen_x, screen_y, screen_x + screen_w, screen_y + screen_h], 
                   fill=(31, 41, 55, 255))
    
    # Eye symbol - green
    eye_center_x, eye_center_y = 32, 29
    draw.ellipse([eye_center_x-4, eye_center_y-3, eye_center_x+4, eye_center_y+3], 
                 fill=(16, 185, 129, 255))
    draw.ellipse([eye_center_x-1.5, eye_center_y-1.5, eye_center_x+1.5, eye_center_y+1.5], 
                 fill=(31, 41, 55, 255))
    
    # Connection dots - white
    dots = [(12, 45), (52, 45), (32, 52)]
    for x, y in dots:
        draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255, 255))
    
    # Pulse line - green
    pulse_points = [(22, 29), (26, 29), (28, 25), (30, 33), (32, 25), (34, 33), (36, 29), (42, 29)]
    for i in range(len(pulse_points)-1):
        draw.line([pulse_points[i], pulse_points[i+1]], fill=(16, 185, 129, 255), width=2)
    
    # Save as ICO
    img.save('icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("Icon created: icon.ico")
    
    # Also save as PNG for web use
    img.save('icon.png', format='PNG')
    print("Icon created: icon.png")

if __name__ == "__main__":
    create_syswatch_icon()