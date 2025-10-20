# AssetNest

## TODO

### Dashboard

- [x] 총 현금자산 업데이트 방식 수정

### DB

- [ ] DB initialize
- [ ] DB 구조 최적화
- [ ] 펀드에 대한 처리 방안
  - [ ] 기준가의 활용 방안
  - [ ] 가격 업데이트 방안
- [ ] asset_type, region_type을 자동으로 추가하는 방법?

### API

- [x] symbol table 업데이트하는 API 추가
- [ ] 예수금 계산시 최신 환율 반영

### Features

- [x] 포트폴리오 분배 비율 대쉬보드
- [ ] 포트폴리오 개요 대쉬보드 - 현금 업데이트 내용 반영

### Test

- [x] API 테스트
- [ ] 대쉬보드 테스트
- [ ] Podman compose 테스트

### Deploy

- [x] Podman compose 추가
- [ ] Makefile에 deploy 추가
