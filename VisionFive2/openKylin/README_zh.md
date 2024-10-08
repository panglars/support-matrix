# openKylin 2.0-RC VisionFive 2 版本测试报告

## 测试环境

### 操作系统信息

- 系统版本：openKylin 2.0-RC
- 下载链接：https://mirror.iscas.ac.cn/openkylin-cdimage/2.0-RC/openKylin-2.0-rc-visionfive2-riscv64.img.xz
- 参考安装文档：https://docs.openkylin.top/zh/01_%E5%AE%89%E8%A3%85%E5%8D%87%E7%BA%A7%E6%8C%87%E5%8D%97/%E5%9C%A8riscv%E4%B8%8A%E5%AE%89%E8%A3%85/%E5%9C%A8VisionFive2%E4%B8%8A%E5%AE%89%E8%A3%85openKylin

### 硬件信息

- StarFive VisionFive 2
- USB 电源适配器一个
- USB-A to C 或 C to C 线缆一条
- microSD 卡一张
- USB to UART 调试器一个（如：CH340, CH341, FT2232 等）
- 杜邦线三根

## 安装步骤

### 解压并刷写镜像到 microSD 卡

假定 `/dev/sdc` 为存储卡。

```bash
xz -d openKylin-2.0-rc-visionfive2-riscv64.img.xz
sudo dd if=openKylin-2.0-rc-visionfive2-riscv64.img of=/dev/sdc bs=1M status=progress
```

### 引导模式选择

StarFive VisionFive 2 提供了多种引导模式，可在上电前通过板载拨码开关进行配置；开发板本体上亦有丝印标注。

为了启动 openKylin 镜像，选择 1-bit QSPI Nor Flash 模式（即：`RGPIO_0 = 0`, `RGPIO_1 = 0`）。注意，此模式可能需要提前更新 Flash 内的固件，若启动不成功，请参考官方文档进行固件升级：[更新 SPL 和 U-Boot](https://doc.rvspace.org/VisionFive2/Quick_Start_Guide/VisionFive2_QSG/spl_u_boot_0.html)

### 登录系统

通过串口登录系统。

默认用户名：`openkylin`
默认密码：`openkylin`

## 预期结果

系统正常启动，能够通过图形界面登录。

## 实际结果

系统正常启动，成功通过图形界面登录。

### 启动信息

屏幕录像（从刷写镜像到登录系统）：
[![asciicast](https://asciinema.org/a/Z8aZ2CJ7loP9PE6KKpUc2cvwd.svg)](https://asciinema.org/a/Z8aZ2CJ7loP9PE6KKpUc2cvwd)

```log
openkylin@openkylin:~$ uname -a
Linux openkylin 6.6.20+ #1 SMP Thu May  9 22:49:32 CST 2024 riscv64 riscv64 riscv64 GNU/Linux
openkylin@openkylin:~$ cat /etc/os-release 
NAME="openKylin"
FULL_NAME="openKylin"
VERSION="2.0 (nile)"
VERSION_US="2.0 (nile)"
ID=openkylin
PRETTY_NAME="openKylin 2.0"
VERSION_ID="2.0"
HOME_URL="https://www.openkylin.top/"
VERSION_CODENAME=nile
PRODUCT_FEATURES=3
openkylin@openkylin:~$ 

```

![login](./image.png)

## 软件包测试结果

| 软件包       | 种类    | 手动测试 |
|:-------------|:--------|:---------|
| apache       | package | ✅       |
| clang        | package | ✅       |
| cmake        | package | ✅       |
| docker       | package |          |
| erlang       | package | ✅       |
| gcc          | package | ✅       |
| gdb          | package | ✅       |
| golang       | package | ✅       |
| haproxy      | package | ✅       |
| libmemcached | package | ✅       |
| lighttpd     | package |          |
| llvm         | package | ✅       |
| mariadb      | package |          |
| nginx        | package | ✅       |
| nodejs       | package | ✅       |
| numpy        | package | ✅       |
| ocaml        | package | ✅       |
| openjdk      | package | ✅       |
| perl         | package | ✅       |
| python       | package | ✅       |
| ruby         | package | ✅       |
| rust         | package | ✅       |
| sqlite       | package | ✅       |
| varnish      | package |          |
| openssl      | package | ✅       |
| postgresql   | package |          |
| redis        | package | ✅       |
| runc         | package |          |
| scipy        | package | ✅       |
| squid        | package |          |
| zookeeper    | package |          |

### godot

需要加入启动参数
```
--display-driver wayland opengl_es3
```

项目管理器
![godot project manager](./godot1.png)

编辑器与游戏运行
![godot editor](./godot2.png)


## 测试判定标准

测试成功：实际结果与预期结果相符。

测试失败：实际结果与预期结果不符。

## 测试结论

测试成功。
