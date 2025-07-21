# DJI Cloud API

## What is the DJI Cloud API?

The launch of the Cloud API mainly solves the problem of developers reinventing the wheel. For developers who do not need in-depth customization of APP, they can directly use DJI Pilot2 to communicate with the third cloud platform, and developers can focus on the development and implementation of cloud service interfaces.

## Docker

If you don't want to install the development environment, you can try deploying with docker. [Click the link to download.](https://terra-sz-hc1pro-cloudapi.oss-cn-shenzhen.aliyuncs.com/c0af9fe0d7eb4f35a8fe5b695e4d0b96/docker/cloud_api_sample_docker.zip)

## Usage

For more documentation, please visit the [DJI Developer Documentation](https://developer.dji.com/doc/cloud-api-tutorial/cn/).

## Latest Release

Cloud API 1.10.0 was released on 7 April 2024. For more information, please visit the [Release Note](https://developer.dji.com/doc/cloud-api-tutorial/cn/).

## License

Cloud API is MIT-licensed. Please refer to the LICENSE file for more information.

## 7/15更新提示（熊泽仁）

新增文件：
```
    src\components\webrtcplayer.vue     WebRtc播放器
```
修改文件：
```
    src\api\http\config.ts      路由ip相关设置
    src\components\StreamSettings.vue       推流相关设置区
    src\pages\page-web\projects\livestream-srs.vue      组件集成
    src\components\MediaPanel.vue       文件管理
```

