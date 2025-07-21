export const CURRENT_CONFIG = {

  // license
  appId: '159636', // You need to go to the development website to apply.
  appKey: '5391c98d927554d7b1e075321e52616', // You need to go to the development website to apply.
  appLicense: 'JgfYxZkzFL8Uarro4eF+GVgNA89GTWJKFBSXm/jGOeGdAtGE5odqsCtJn/Fqxfn9bfXYY0ERF4psruVH5ilprcHAGHJvcJC4N3glBLeKOVru1g2JaVEQ9tNG05X+s53+5NBxgHfzCT0FXkmoiCa5rxSoujHjG3jROTZgSJzlgnI=', // You need to go to the development website to apply.

  // http
  baseURL: 'http://localhost:6789/', // This url must end with "/". Example: 'http://192.168.1.1:6789/'修改
  websocketURL: 'http://localhost:6789/api/v1/ws', // Example: 'ws://192.168.1.1:6789/api/v1/ws'
  minioURL: 'http://192.168.101.7:9001/', // minio服务器地址
  // livestreaming
  // RTMP  Note: This IP is the address of the streaming server. If you want to see livestream on web page, you need to convert the RTMP stream to WebRTC stream.
  rtmpURL: 'http://127.0.0.1:1985/rtc/v1/whip/?app=live&stream=test', // Example: 'rtmp://192.168.1.1/live/'

  aiServiceURL: 'http://192.168.101.10:8000', // 新增！FastAPI 控制端
  aiWebSocketURL: 'ws://192.168.101.10:8000', // 新增！FastAPI 控制端

  rtmpPrefix: 'rtmp://127.0.0.1/live/',
  webrtcPrefix: 'http://127.0.0.1:1985/rtc/v1/whip/?app=live&stream=',
  flvPrefix: 'http://127.0.0.1:8081/live/',
  webrtc: 'webrtc://192.168.101.10/live/',

  // // GB28181 Note:If you don't know what these parameters mean, you can go to Pilot2 and select the GB28181 page in the cloud platform. Where the parameters same as these parameters.
  // gbServerIp: 'Please enter the server ip.',
  // gbServerPort: 'Please enter the server port.',
  // gbServerId: 'Please enter the server id.',
  // gbAgentId: 'Please enter the agent id',
  // gbPassword: 'Please enter the agent password',
  // gbAgentPort: 'Please enter the local port.',
  // gbAgentChannel: 'Please enter the channel.',
  // // RTSP
  // rtspUserName: 'Please enter the username.',
  // rtspPassword: 'Please enter the password.',
  // rtspPort: '8554',
  // // Agora
  // agoraAPPID: 'Please enter the agora app id.',
  // agoraToken: 'Please enter the agora temporary token.',
  // agoraChannel: 'Please enter the agora channel.',

  // map
  // You can apply on the AMap website.
  amapKey: '5ab81f1a59bd73ed8e3c9e49ae85ac8d',

}
