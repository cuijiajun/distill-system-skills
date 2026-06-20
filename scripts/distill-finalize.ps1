# distill-finalize.ps1
# 蒸馏收尾脚本：自动完成 step 8/9/10 的全部机械操作 + 自检
# 用法：powershell -ExecutionPolicy Bypass -File distill-finalize.ps1 -DistilledDir "E:\xxx\distilled" [-ProjectRoot "E:\xxx"]
# 如果不传 -ProjectRoot，默认取 DistilledDir 的父目录

param(
    [Parameter(Mandatory=$true)]
    [string]$DistilledDir,
    [string]$ProjectRoot
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 自动推断 ProjectRoot
if(-not $ProjectRoot){
    $ProjectRoot = Split-Path $DistilledDir -Parent
}

# 定位 skill 目录（脚本在 scripts/ 下，skill 根在父目录）
$SkillRoot = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent
$ViewerSrc = "$SkillRoot\assets\viewer.html"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  蒸馏收尾脚本 (distill-finalize)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DistilledDir: $DistilledDir"
Write-Host "  ProjectRoot:  $ProjectRoot"
Write-Host "  SkillRoot:    $SkillRoot"
Write-Host ""

if(-not (Test-Path $DistilledDir)){
    Write-Host "[FATAL] distilled 目录不存在: $DistilledDir" -ForegroundColor Red
    exit 1
}

$checks = @()

# ============================================================
# Step 8: 检查 capabilities.json 是否存在（AI 应已生成）
# ============================================================
$capPath = "$DistilledDir\capabilities.json"
if(Test-Path $capPath){
    try {
        $cap = Get-Content $capPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $toolCount = $cap.tools.Count
        $sysName = $cap.system
        $sysDesc = $cap.description
        $checks += [PSCustomObject]@{Step="8"; File="capabilities.json"; Status="OK"; Detail="$toolCount tools"}
        Write-Host "[Step 8] capabilities.json OK ($toolCount tools)" -ForegroundColor Green
    } catch {
        $checks += [PSCustomObject]@{Step="8"; File="capabilities.json"; Status="FAIL"; Detail="JSON 解析失败: $($_.Exception.Message)"}
        Write-Host "[Step 8] capabilities.json JSON 解析失败: $($_.Exception.Message)" -ForegroundColor Red
        # 尝试不转换直接读
        $cap = Get-Content $capPath -Raw -Encoding UTF8
        $toolCount = 0
        $sysName = "蒸馏项目"
        $sysDesc = ""
    }
} else {
    $checks += [PSCustomObject]@{Step="8"; File="capabilities.json"; Status="MISSING"; Detail="AI 未生成 capabilities.json"}
    Write-Host "[Step 8] capabilities.json 不存在！AI 跳过了 step 8。" -ForegroundColor Red
    $toolCount = 0
    $sysName = "蒸馏项目"
    $sysDesc = ""
}

# ============================================================
# Step 9a: 拷贝 viewer.html -> index.html
# ============================================================
$indexPath = "$DistilledDir\index.html"
if(Test-Path $ViewerSrc){
    Copy-Item -LiteralPath $ViewerSrc -Destination $indexPath -Force
    $checks += [PSCustomObject]@{Step="9a"; File="index.html"; Status="OK"; Detail="$([math]::Round((Get-Item $indexPath).Length/1KB,1))KB"}
    Write-Host "[Step 9a] index.html OK (已拷贝 viewer.html)" -ForegroundColor Green
} else {
    $checks += [PSCustomObject]@{Step="9a"; File="index.html"; Status="FAIL"; Detail="viewer.html 源不存在: $ViewerSrc"}
    Write-Host "[Step 9a] viewer.html 源不存在: $ViewerSrc" -ForegroundColor Red
}

# ============================================================
# Step 9b: 生成 data.js（内嵌全部文档 + 大模型配置）
# ============================================================
$dataJsPath = "$DistilledDir\data.js"

# 收集所有 .md/.json/.txt 文件
$files = Get-ChildItem -Path $DistilledDir -Recurse -File | Where-Object { $_.Extension -in '.md','.json','.txt' } | Sort-Object FullName

if($files.Count -eq 0){
    $checks += [PSCustomObject]@{Step="9b"; File="data.js"; Status="FAIL"; Detail="distilled/ 下无 .md/.json 文件"}
    Write-Host "[Step 9b] distilled/ 下无文件可嵌入！" -ForegroundColor Red
} else {
    # 预计算 domainCount
    $domainCount = 0
    $domainDir = "$DistilledDir\domain"
    if(Test-Path $domainDir){
        $domainCount = (Get-ChildItem -Path $domainDir -File -Filter "*.md" -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne '_index.md' }).Count
    }

    # 构建文件数组（使用 ConvertTo-Json 确保转义正确）
    $fileList = @()
    foreach($f in $files){
        $rel = $f.FullName.Substring($DistilledDir.Length + 1) -replace '\\','/'
        $text = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
        $fileList += [PSCustomObject]@{ path = $rel; text = $text }
    }

    # 读取大模型配置
    $settings = $null
    $ocPaths = @(
        "$env:USERPROFILE\.joyincode\opencode.json",
        "$env:USERPROFILE\.config\opencode\opencode.json"
    )
    foreach($ocPath in $ocPaths){
        if(Test-Path $ocPath){
            try {
                $oc = Get-Content $ocPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $modelName = ($oc.model -split '/' | Select-Object -Last 1)
                $provName = ($oc.provider | Get-Member -MemberType NoteProperty)[0].Name
                $prov = $oc.provider.$provName.options
                $settings = [PSCustomObject]@{
                    endpoint = $prov.baseURL
                    apiKey = $prov.apiKey
                    model = $modelName
                    temperature = 0.3
                }
                Write-Host "[Step 9b] 大模型配置来源: $ocPath (model=$modelName)" -ForegroundColor DarkGray
                break
            } catch {
                Write-Host "[Step 9b] 读取 $ocPath 失败: $($_.Exception.Message)" -ForegroundColor DarkGray
            }
        }
    }

    # 生成 data.js
    $dataObj = [PSCustomObject]@{
        name = $sysName
        description = $sysDesc
        toolCount = $toolCount
        domainCount = $domainCount
        files = $fileList
    }

    $js = "window.__DISTILLED_DATA__ = " + ($dataObj | ConvertTo-Json -Depth 5 -Compress) + ";`n"
    if($settings){
        $js += "`nwindow.__DISTILLED_SETTINGS__ = " + ($settings | ConvertTo-Json -Compress) + ";`n"
    }

    [System.IO.File]::WriteAllText($dataJsPath, $js, [System.Text.UTF8Encoding]::new($false))
    $dataSize = [math]::Round((Get-Item $dataJsPath).Length/1KB,1)
    $checks += [PSCustomObject]@{Step="9b"; File="data.js"; Status="OK"; Detail="$dataSize KB ($($files.Count) 文件, toolCount=$toolCount)"}
    Write-Host "[Step 9b] data.js OK ($dataSize KB, $($files.Count) 文件嵌入)" -ForegroundColor Green
}

# ============================================================
# Step 10: 创建/更新项目根 AGENTS.md
# ============================================================
$agentsPath = "$ProjectRoot\AGENTS.md"
$agentsContent = @"
## 蒸馏文档（AI 能力说明）
本系统已蒸馏为 AI 可用的领域能力文档，位于 `distilled/`。
- 系统能力入口：`distilled/AGENTS.md`（API 清单 + curl 示例 + 编排）
- 查看器/对话：双击 `distilled/index.html`（已内嵌全部文档+大模型配置，开箱即用）
- 涉及本系统业务时，先读 `distilled/00-overview.md` 了解系统能力。
"@

$needWrite = $true
if(Test-Path $agentsPath){
    $existing = Get-Content $agentsPath -Raw -Encoding UTF8
    if($existing -match '蒸馏文档'){
        $needWrite = $false
        $checks += [PSCustomObject]@{Step="10"; File="AGENTS.md"; Status="OK"; Detail="已存在蒸馏引用"}
        Write-Host "[Step 10] AGENTS.md 已含蒸馏引用，跳过" -ForegroundColor Green
    }
}

if($needWrite){
    if(Test-Path $agentsPath){
        # 追加到已有 AGENTS.md
        Add-Content -LiteralPath $agentsPath -Value "`n$agentsContent" -Encoding UTF8
        $checks += [PSCustomObject]@{Step="10"; File="AGENTS.md"; Status="OK"; Detail="已追加蒸馏引用"}
        Write-Host "[Step 10] AGENTS.md 已追加蒸馏引用" -ForegroundColor Green
    } else {
        # 新建
        [System.IO.File]::WriteAllText($agentsPath, $agentsContent + "`n", [System.Text.UTF8Encoding]::new($false))
        $checks += [PSCustomObject]@{Step="10"; File="AGENTS.md"; Status="OK"; Detail="已新建"}
        Write-Host "[Step 10] AGENTS.md 已新建" -ForegroundColor Green
    }
}

# ============================================================
# 收尾验证门
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  收尾验证门" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$allPass = $true
foreach($c in $checks){
    $icon = switch($c.Status){
        "OK" { "✅"; $color="Green" }
        "FAIL" { "❌"; $color="Red"; $allPass=$false }
        "MISSING" { "❌"; $color="Red"; $allPass=$false }
    }
    Write-Host ("  {0} Step {1}: {2,-22} {3}" -f $icon, $c.Step, $c.File, $c.Detail) -ForegroundColor $color
}

Write-Host ""
if($allPass){
    Write-Host "✅ 蒸馏完成！全部文件就位。" -ForegroundColor Green
    Write-Host "   预览: file:///$( $DistilledDir -replace '\\','/' )/index.html" -ForegroundColor Cyan
} else {
    Write-Host "❌ 蒸馏未完成！有文件缺失或失败，请修复后重跑。" -ForegroundColor Red
    Write-Host "   缺 capabilities.json = AI 未完成 step 8，需重新蒸馏"
    Write-Host "   缺 index.html/data.js = 脚本拷贝/生成失败，检查 skill 目录"
}
Write-Host ""
