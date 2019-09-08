# falkon-pyqt5
falkon rewrite with pyqt5

## Why use PyQt5 to rewrite Falkon
In short, Python development efficiency is faster than C++, saving time and effort.

### Why do I need a basic browser?
* Mobile software is more popular than desktop software
* PC software tends to be webpaged
* Webpage H5 2D 3D technology has partially replaced desktop software
* Desktop H5 program requires a shell
* The following features are required for the shell of complex data presentation
   * Similar to Chrome's interactive features, including removable tabs, detachable tabs
   * File access feature, file downloader for downloading large files
   * Plugin extensions, which can be quickly extended based on browser
   * Low development cost scalability

### Why use Falkon
* From a cross-platform perspective, Qt is the best choice for desktop cross-platform (program size is not a fatal flaw)
* The features of Falkon in the browser developed by Qt PyQt are more comprehensive, and the features do not need to rethink the structure and implementation.

### PyQt5 Efficiency issues after rewriting
* Because the Qt browser component is the WebKit core that uses the Chromium project, the efficiency of the browser parsing and rendering HTML is theoretically the same as Chromium
* The other interaction frequency of the browser is not high, and the efficiency of using PyQt and C++ Qt should be almost the same.

### Why should I rewrite?
* The first reason is that the C++ project compiles for a long time and wastes development time. The laptop CPU I use is not fast enough for rapid development.
* Python does not need to be compiled, run directly, and develop a lot faster in time.
* Using Python dynamic language features can simplify development complexity without having to solve C++'s cumbersome syntax and memory leaks, pointers, etc.
* Debugging with Python is easier than GDB

## How to run
* Install PyQt5 and PyQtWebEngine
```
pip install PyQt5
pip install PyQtWebEngine
```
*Set the environment
```
# Running under Windows
env.bat
# Running under Linux
source env.sh
```
* Run the program
```
python mc\main\main.py
```

# falkon-pyqt5
Falkon 使用 PyQt5 重写

## 为什么用 PyQt5 重写 Falkon
简单来说 Python 的开发效率比 C++ 快，省时省力省钱

### 为什么需要一个基础的浏览器
* 移动软件比桌面软件更流行
* PC软件趋向于网页化
* 网页H5 2D 3D技术已经部分取代桌面软件
* 桌面H5程序需要一个外壳
* 对于复杂数据展示的外壳需要以下几个特性
   * 类似Chrome的交互特性，包括可移动tab，可分离tab
   * 文件访问特性，文件下载器，用于下载大文件
   * 插件扩展，可以基于浏览器快速扩展功能
   * 低开发成本的扩展性

### 为什么使用 Falkon
* 从跨平台的角度看，Qt 是桌面跨平台的最佳选择（程序大小已经不是致命缺点）
* Qt PyQt 开发的浏览器中 Falkon 的特性比较全面，特性不用重新考虑结构和实现

### PyQt5 重写后的效率问题
* 因为 Qt 浏览器组件是使用了 Chromium 项目的 WebKit 核心，因此浏览器解析和渲染 HTML 的效率理论上与 Chromium 相同
* 浏览器的其他交互频率不高，使用PyQt 与C++ Qt的效率应该几乎一致

### 为什么要重写
* 第一个原因是 C++ 项目编译的时间很长，浪费开发时间，我一般使用的笔记本电脑CPU不足以快速开发
* 而Python不需要编译，直接运行，开发上时间上快很多
* 用Python动态语言的特性可以简化开发复杂度，不必解决C++繁琐的语法以及内存泄露，指针等问题
* 用Python的调试方式比GDB方便

## 如何运行
* 安装PyQt5 以及 PyQtWebEngine
```
pip install PyQt5
pip install PyQtWebEngine
```
* 设置环境
```
# Windows 下运行
env.bat
# 或者 Linux 下运行
source env.sh
```
* 运行程序
```
python mc\main\main.py
```
