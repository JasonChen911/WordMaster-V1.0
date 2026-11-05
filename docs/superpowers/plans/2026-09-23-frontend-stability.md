# 前端资源与桌面生命周期稳定性修复

用户已明确授权直接实施。保留 React.lazy，修复产物发布、服务实例和缓存的一致性。

- [ ] 复现：运行服务中旧 Games 哈希 404、新哈希 200；HTML 缺少缓存策略。
- [ ] 构建：Vite 输出唯一暂存目录，检查全部 JS/CSS 引用，生成带 SHA256 的构建清单，先发布不可变文件，最后原子替换 index.html。保留旧 hashed assets，失败不触碰当前入口。
- [ ] 服务：从文件自身位置解析 dist，不回退开发源码。启动读入校验后的完整前端快照（当前约 2.7MB），进程内不随磁盘重建改变；HTML 禁缓存，hash assets immutable，缺失静态文件真实 404。
- [ ] 启动：预绑定 socket 消除端口探测竞争；识别已占用服务并选新端口；health 校验启动 UUID/build ID，再检查首页及资源 HTTP 200 才创建 WebView；退出显式停止 uvicorn 并释放 socket。
- [ ] 恢复：早于入口模块安装错误监听；dynamic import/Vite preload/入口加载失败按构建 ID 在 sessionStorage 仅恢复一次。保留错误页与手动刷新，存储不可用时禁止自动循环。
- [ ] 日志：logs/frontend.log 只写版本、build、路径、端口、加载类别、净化后的资产文件名，不写业务/查询串/密钥。
- [ ] 打包：主程序严格验证当前 build；安装器使用新暂存 bundle，缺主 EXE 即失败；记录 EXE SHA256 及 build ID。
- [ ] 验收：故障回归、真实全部懒加载路由、运行中重建/刷新、5次服务与桌面启动关闭、最终 EXE 与安装器内容一致性。
