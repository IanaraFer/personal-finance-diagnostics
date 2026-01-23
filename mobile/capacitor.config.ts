import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.financediag.app',
  appName: 'Finance Diagnostics',
  webDir: 'www',
  server: {
    androidScheme: 'https'
  }
};

export default config;
