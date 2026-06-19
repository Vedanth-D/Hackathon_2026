# Generate placeholder JPEG images for dataset cases
$dirs = @(
    "dataset\images\sample\case_s01",
    "dataset\images\sample\case_s02",
    "dataset\images\sample\case_s03",
    "dataset\images\sample\case_s04",
    "dataset\images\sample\case_s05",
    "dataset\images\sample\case_s06",
    "dataset\images\test\case_001",
    "dataset\images\test\case_002",
    "dataset\images\test\case_003",
    "dataset\images\test\case_004",
    "dataset\images\test\case_005",
    "dataset\images\test\case_006",
    "dataset\images\test\case_007",
    "dataset\images\test\case_008",
    "dataset\images\test\case_009",
    "dataset\images\test\case_010"
)

Add-Type -AssemblyName System.Drawing

function New-ClaimImage($path, $label, $hasDamage) {
    $dir = Split-Path $path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $bmp = New-Object System.Drawing.Bitmap 640, 480
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(240, 240, 240))
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(160, 160, 160))
    $g.FillRectangle($brush, 80, 80, 480, 320)
    $font = New-Object System.Drawing.Font("Arial", 14)
    $g.DrawString($label, $font, [System.Drawing.Brushes]::Black, 100, 100)
    if ($hasDamage) {
        $red = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(200, 50, 50))
        $g.FillEllipse($red, 300, 200, 80, 80)
    }
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $g.Dispose(); $bmp.Dispose()
}

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

New-ClaimImage "dataset\images\sample\case_s01\img_1_door_scratch.jpg" "door scratch" $true
New-ClaimImage "dataset\images\sample\case_s01\img_2_door_context.jpg" "door context" $false
New-ClaimImage "dataset\images\sample\case_s02\img_1_bumper_dent.jpg" "bumper dent" $true
New-ClaimImage "dataset\images\sample\case_s03\img_1_screen_crack.jpg" "screen crack" $true
New-ClaimImage "dataset\images\sample\case_s04\img_1_box_crush.jpg" "box crush" $true
New-ClaimImage "dataset\images\sample\case_s04\img_2_box_corner.jpg" "box corner" $true
New-ClaimImage "dataset\images\sample\case_s05\img_1_door_clean.jpg" "door no_damage clean" $false
New-ClaimImage "dataset\images\sample\case_s06\img_1_blur.jpg" "blur unreadable" $false

New-ClaimImage "dataset\images\test\case_001\img_1_door_scratch.jpg" "door scratch" $true
New-ClaimImage "dataset\images\test\case_001\img_2_door_context.jpg" "door context" $false
New-ClaimImage "dataset\images\test\case_002\img_1_bumper_dent.jpg" "bumper dent" $true
New-ClaimImage "dataset\images\test\case_003\img_1_screen_crack.jpg" "screen crack" $true
New-ClaimImage "dataset\images\test\case_004\img_1_box_torn.jpg" "box torn" $true
New-ClaimImage "dataset\images\test\case_005\img_1_box_crush.jpg" "box crush" $true
New-ClaimImage "dataset\images\test\case_005\img_2_box_corner.jpg" "box corner" $true
New-ClaimImage "dataset\images\test\case_006\img_1_windshield_shatter.jpg" "windshield shatter" $true
New-ClaimImage "dataset\images\test\case_007\img_1_hood_clean.jpg" "hood no_damage clean" $false
New-ClaimImage "dataset\images\test\case_008\img_1_keyboard_damage.jpg" "keyboard broken" $true
New-ClaimImage "dataset\images\test\case_009\img_1_blur.jpg" "blur unreadable" $false
New-ClaimImage "dataset\images\test\case_010\img_1_wrong_object.jpg" "wrong object phone" $false

Write-Host "Images created."
