# 流式检查大JSON文件中每个对象的tr和totalChildren是否相等

$path = "D:\social_simulation_engine\data\data\3weibo_data_index_group_importance_withvirtual.json"
$reader = [System.IO.StreamReader]::new($path)

# 跳过开头的[
$line = $reader.ReadLine()
$allEqual = $true
while (($line = $reader.ReadLine()) -ne $null) {
    $line = $line.Trim()
    if ($line -eq ']' -or $line -eq '') { break }
    # 去掉结尾的逗号
    if ($line.EndsWith(',')) { $line = $line.Substring(0, $line.Length-1) }
    try {
        $obj = $line | ConvertFrom-Json
        if ($obj.tr -ne $obj.totalChildren) {
            Write-Output $false
            $reader.Close()
            exit
        }
    } catch {}
}
$reader.Close()
Write-Output $true 