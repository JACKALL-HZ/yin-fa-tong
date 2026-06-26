# 支付宝沙箱密钥

此目录用于存放支付宝沙箱环境的 RSA 密钥文件（可选）。

## 获取方式

1. 登录 https://openhome.alipay.com
2. 进入应用 → 开发设置 → 接口加签方式
3. 使用支付宝密钥生成器生成 RSA2 密钥对
4. 将应用公钥粘贴到开放平台，获取支付宝公钥

## 配置方式

将私钥和支付宝公钥配置到 `.env` 文件的 `ALIPAY_PRIVATE_KEY` 和 `ALIPAY_PUBLIC_KEY` 字段。
