# Bianbu BIT-BRICK K1 测试报告

## 测试环境

### 系统信息

- 下载链接：https://archive.spacemit.com/image/k1/version/bianbu-computer/v3.0beta1/
- 参考安装文档：https://docs.bit-brick.com/docs/k1/getting-started/preparation

### 硬件信息

- BIT-BRICK K1
- 电源适配器
- microSD 卡一张
- USB to UART 调试器一个

## 安装步骤

### 刷写镜像（sd 卡）

**请务必选择以 `.img.zip` 结尾的压缩包**
下载并解压镜像后，使用 `dd` 将镜像写入 microSD 卡。

```bash
unzip bianbu-computer-s1_v2.1.5.img.zip
sudo dd if=bianbu-computer-s1_v2.1.5.img of=/dev/sdX bs=1M status=progress 
```

### 登录系统

通过串口登录系统。

默认用户名： `root`
默认密码： `bianbu`


## 实际结果

### 启动信息

```log

Bianbu 3.0beta1 k1 ttyS0
k1 login: root
密码：
Welcome to Bianbu 3.0beta1 (GNU/Linux 6.6.63 riscv64)

 * Documentation:  https://bianbu.spacemit.com
 * Support:        https://ticket.spacemit.com

root@k1:~# uname -a
Linux k1 6.6.63 #2.2.7.3+20250917010805 SMP PREEMPT Tue Sep 16 19:38:16 UTC 2025 riscv64 riscv64 riscv64 GNU/Linux
root@k1:~# cat /etc/os-release
PRETTY_NAME="Bianbu Star 3.0beta1"
NAME="Bianbu"
VERSION_ID="3.0beta1"
VERSION="3.0beta1 (Plucky Puffin)"
VERSION_CODENAME=plucky
ID=bianbu
ID_LIKE=debian
HOME_URL="https://bianbu.spacemit.com"
SUPPORT_URL="https://bianbu.spacemit.com"
BUG_REPORT_URL="https://ticket.spacemit.com"
PRIVACY_POLICY_URL="https://www.spacemit.com/privacy-policy"
UBUNTU_CODENAME=plucky
LOGO=bianbu-logo
```

## 桌面环境

![](./star_setup.jpeg)

## 测试结论

系统正常启动，成功通过串口及图形界面登录。
