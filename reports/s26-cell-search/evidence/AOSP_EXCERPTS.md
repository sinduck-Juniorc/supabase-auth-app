# AOSP 근거 발췌

조사 종료 전에 저장한 원본 중 판단과 직접 관련된 짧은 지점만 발췌했다. 검토 중 과도하게 포함된 다른 API 발췌를 제거했다. 새 외부 조사는 수행하지 않았다. AOSP main은 삼성 출하 펌웨어와 동일하다고 가정하지 않는다. 원본 URL·전체 파일 해시는 aosp-sources.json 참조.

## shell_manifest

```text
257:     <uses-permission android:name="android.permission.MODIFY_PHONE_STATE" />
260:     <!-- Shell only holds android.permission.NETWORK_SCAN in order to to enable CTS testing -->
261:     <uses-permission android:name="android.permission.NETWORK_SCAN" />
525:     <uses-permission android:name="android.permission.LOCATION_HARDWARE" />
```

## location_service

```text
1134:     @android.annotation.EnforcePermission(allOf={android.Manifest.permission.LOCATION_HARDWARE, android.Manifest.permission.ACCESS_FINE_LOCATION})
1135:     @Override
1136:     public void injectLocation(Location location) {
1137: 
1138:         super.injectLocation_enforcePermission();
1139: 
1140:         Preconditions.checkArgument(location.isComplete());
1141: 
1142:         int userId = UserHandle.getCallingUserId();
1143:         LocationProviderManager manager = getLocationProviderManager(location.getProvider());
1144:         if (manager != null && manager.isEnabled(userId)) {
1145:             manager.injectLastLocation(Objects.requireNonNull(location), userId);
1146:         }
1147:     }
```

## phone_service

```text
7180:     public int requestNetworkScan(int subId, boolean renounceFineLocationAccess,
7181:             NetworkScanRequest request, Messenger messenger,
7182:             IBinder binder, String callingPackage, String callingFeatureId) {
7183:         TelephonyPermissions.enforceCallingOrSelfModifyPermissionOrCarrierPrivilege(
7184:                 mApp, subId, "requestNetworkScan");
7185:         LocationAccessPolicy.LocationPermissionResult locationResult =
7186:                 LocationAccessPolicy.LocationPermissionResult.DENIED_HARD;
```

## gnss_provider

```text
838:     private void injectLocation(Location location) {
839:         if (!location.isMock()) {
840:             mGnssNative.injectLocation(location);
841:         }
842:     }
1164:         } else if ("force_time_injection".equals(command)) {
1165:             demandUtcTimeInjection();
1166:         } else if ("force_psds_injection".equals(command)) {
1167:             if (mSupportsPsds) {
1168:                 postWithWakeLockHeld(() -> handleDownloadPsdsData(
1169:                         GnssPsdsDownloader.LONG_TERM_PSDS_SERVER_INDEX));
1170:             }
1171:         } else if ("request_power_stats".equals(command)) {
```

## gnss_aidl

```text
248:     void injectLocation(in GnssLocation location);
258:     void injectBestLocation(in GnssLocation location);
```

## telephony_hal

```text
473:     void startNetworkScan(in int serial, in NetworkScanRequest request);
```

## permissions

```text
2132:     <permission android:name="android.permission.LOCATION_HARDWARE"
2133:         android:protectionLevel="signature|privileged|role" />
3004:     <permission android:name="android.permission.MODIFY_PHONE_STATE"
3005:         android:protectionLevel="signature|privileged|role" />
```
