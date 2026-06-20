// 蒸馏数据自动加载文件（蒸馏时自动生成，勿手动编辑）
// index.html 会自动读取本文件，加载后无需手动选目录
window.__DISTILLED_DATA__ = {
  name: "<系统名>",
  description: "<一句话系统描述>",
  toolCount: 0,       // ← 预计算：capabilities.json 的 tools 数组长度
  domainCount: 0,     // ← 预计算：domain/ 目录下非 _index.md 的文件数
  files: [
    // 每个元素 = 一个 distilled/ 下的文件
    // path 为相对路径，text 为文件完整内容
    // 示例：
    // { path: "00-overview.md", text: "# 系统名..." },
    // { path: "domain/user.md", text: "..." },
    // { path: "capabilities.json", text: "..." }
  ]
};
// 大模型设置（读取 ~/.joyincode/opencode.json，无则省略整段）
window.__DISTILLED_SETTINGS__ = {
  endpoint: "<provider baseURL>",
  apiKey: "<provider apiKey>",
  model: "<model 名，去掉 provider 前缀>",
  temperature: 0.3
};
