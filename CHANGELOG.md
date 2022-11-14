# Changelog

All notable changes to this project will be documented in this file. See
[Conventional Commits](https://conventionalcommits.org) for commit guidelines.

## [3.2.0](https://github.com/emma-simbot/experience-hub/compare/v3.1.0...v3.2.0) (2022-11-14)


### Features

* migrate the response templates from the nlg repo ([#140](https://github.com/emma-simbot/experience-hub/issues/140)) ([f01ed30](https://github.com/emma-simbot/experience-hub/commit/f01ed303bef22ccd9565837532c9597902f6ebe2)), closes [#136](https://github.com/emma-simbot/experience-hub/issues/136)

## [3.1.0](https://github.com/emma-simbot/experience-hub/compare/v3.0.1...v3.1.0) (2022-11-14)


### Features

* only extract features when we need them ([#138](https://github.com/emma-simbot/experience-hub/issues/138)) ([85e2f12](https://github.com/emma-simbot/experience-hub/commit/85e2f1254cdcfcf7f34166836f779bbcf54f717b)), closes [#135](https://github.com/emma-simbot/experience-hub/issues/135)

## [3.0.1](https://github.com/emma-simbot/experience-hub/compare/v3.0.0...v3.0.1) (2022-11-14)


### Bug Fixes

* condition when checking whether the agent generated an action ([#139](https://github.com/emma-simbot/experience-hub/issues/139)) ([b525708](https://github.com/emma-simbot/experience-hub/commit/b525708dd85cb5b86a212f7d6028e9fadc0dbda7))

## [3.0.0](https://github.com/emma-simbot/experience-hub/compare/v2.0.0...v3.0.0) (2022-11-14)


### ⚠ BREAKING CHANGES

* **datamodels:** support changes for arena v3 (#137)

### Features

* **datamodels:** support changes for arena v3 ([#137](https://github.com/emma-simbot/experience-hub/issues/137)) ([324559c](https://github.com/emma-simbot/experience-hub/commit/324559c2492a25fdac74dd107ebbf1258dbd277d)), closes [#133](https://github.com/emma-simbot/experience-hub/issues/133) [#134](https://github.com/emma-simbot/experience-hub/issues/134)

## [2.0.0](https://github.com/emma-simbot/experience-hub/compare/v1.13.0...v2.0.0) (2022-11-14)


### ⚠ BREAKING CHANGES

* decouple intent and action prediction into multiple pipelines (#133)

### Features

* decouple intent and action prediction into multiple pipelines ([#133](https://github.com/emma-simbot/experience-hub/issues/133)) ([51ccd84](https://github.com/emma-simbot/experience-hub/commit/51ccd84e6e26aa2be93f3d336ad789aa95bdd0a6))

## [1.13.0](https://github.com/emma-simbot/experience-hub/compare/v1.12.1...v1.13.0) (2022-11-03)


### Features

* add simple feedback for errors from the arena ([#131](https://github.com/emma-simbot/experience-hub/issues/131)) ([14e8e40](https://github.com/emma-simbot/experience-hub/commit/14e8e40dd506a3a63a3ad9eb9631d5e2afb837a2))

## [1.12.1](https://github.com/emma-simbot/experience-hub/compare/v1.12.0...v1.12.1) (2022-11-01)


### Bug Fixes

* enable clarification questions ([51a0208](https://github.com/emma-simbot/experience-hub/commit/51a02081f935393693c6b6fa2a9f2ca0178f77dc))

## [1.12.0](https://github.com/emma-simbot/experience-hub/compare/v1.11.0...v1.12.0) (2022-11-01)


### Features

* add retries when performing healthcheck of clients ([#129](https://github.com/emma-simbot/experience-hub/issues/129)) ([c959e83](https://github.com/emma-simbot/experience-hub/commit/c959e83bafaffc9ff41f12bc233093979724a683))

## [1.11.0](https://github.com/emma-simbot/experience-hub/compare/v1.10.3...v1.11.0) (2022-11-01)


### Features

* refactor cache clients to use `cloudpathlib` instead ([#127](https://github.com/emma-simbot/experience-hub/issues/127)) ([8e6dbc7](https://github.com/emma-simbot/experience-hub/commit/8e6dbc7d8bcf8ba32413f19ffb7bb8adadabad8f)), closes [#120](https://github.com/emma-simbot/experience-hub/issues/120)

## [1.10.3](https://github.com/emma-simbot/experience-hub/compare/v1.10.2...v1.10.3) (2022-10-31)


### Bug Fixes

* healthcheck urls for simbot docker compose ([85a68b1](https://github.com/emma-simbot/experience-hub/commit/85a68b1499885696cb59f34db906c245cbc80477))

## [1.10.2](https://github.com/emma-simbot/experience-hub/compare/v1.10.1...v1.10.2) (2022-10-31)


### Bug Fixes

* service registry file for production simbot services ([1df4a28](https://github.com/emma-simbot/experience-hub/commit/1df4a282d2febb55174339341d8cc890c4171044))

## [1.10.1](https://github.com/emma-simbot/experience-hub/compare/v1.10.0...v1.10.1) (2022-10-31)


### Bug Fixes

* add image versions to the service, not the model ([7f56bc9](https://github.com/emma-simbot/experience-hub/commit/7f56bc9f80c6ed52d4ea032020815f25f0ede797))

## [1.10.0](https://github.com/emma-simbot/experience-hub/compare/v1.9.0...v1.10.0) (2022-10-30)


### Features

* remove intent from `DialogueUtterance` datamodel ([#122](https://github.com/emma-simbot/experience-hub/issues/122)) ([3f1a90a](https://github.com/emma-simbot/experience-hub/commit/3f1a90a5ac4cad057a2a131dcfe30b16da2e6b62))

## [1.9.0](https://github.com/emma-simbot/experience-hub/compare/v1.8.6...v1.9.0) (2022-10-30)


### Features

* include service registry to automatically pull and run correct services ([#121](https://github.com/emma-simbot/experience-hub/issues/121)) ([2c813e4](https://github.com/emma-simbot/experience-hub/commit/2c813e47b835e11d078e80dbd8172c79856bc3ac))

## [1.8.6](https://github.com/emma-simbot/experience-hub/compare/v1.8.5...v1.8.6) (2022-10-27)


### Bug Fixes

* handles when no buttons are detected ([#118](https://github.com/emma-simbot/experience-hub/issues/118)) ([b1aa2dd](https://github.com/emma-simbot/experience-hub/commit/b1aa2dd8eab47a45a81b1302288b6f6d4c484e15))

## [1.8.5](https://github.com/emma-simbot/experience-hub/compare/v1.8.4...v1.8.5) (2022-10-27)


### Bug Fixes

* remove the previous api helpers for simbot intents ([#117](https://github.com/emma-simbot/experience-hub/issues/117)) ([2262ab0](https://github.com/emma-simbot/experience-hub/commit/2262ab09d4bc430df0be3d8ca3ea5c4576b04ca8))

## [1.8.4](https://github.com/emma-simbot/experience-hub/compare/v1.8.3...v1.8.4) (2022-10-25)


### Bug Fixes

* handles case when utterance.intent is `None` ([#115](https://github.com/emma-simbot/experience-hub/issues/115)) ([5c0677f](https://github.com/emma-simbot/experience-hub/commit/5c0677fa80286233e5be0d7b0c7608c5c26d07eb))

## [1.8.3](https://github.com/emma-simbot/experience-hub/compare/v1.8.2...v1.8.3) (2022-10-25)


### Bug Fixes

* send emma policy model the correct intents ([#114](https://github.com/emma-simbot/experience-hub/issues/114)) ([e107140](https://github.com/emma-simbot/experience-hub/commit/e1071407ba769d1bc8189ea3d7fe8e1a5549d7a0))

## [1.8.2](https://github.com/emma-simbot/experience-hub/compare/v1.8.1...v1.8.2) (2022-10-24)


### Bug Fixes

* **NLU pipeline:** return the intent parsed by the NLU, instead of just act ([fd0e3bf](https://github.com/emma-simbot/experience-hub/commit/fd0e3bf2afff443fbadb11d9a654390d8cfc22a3))

## [1.8.1](https://github.com/emma-simbot/experience-hub/compare/v1.8.0...v1.8.1) (2022-10-24)


### Bug Fixes

* ensure turns without an intent are included when getting the environment state history ([#112](https://github.com/emma-simbot/experience-hub/issues/112)) ([17cd399](https://github.com/emma-simbot/experience-hub/commit/17cd399dbfb9d9fbebb4e5bfbbc9b53dc35ff07b))

## [1.8.0](https://github.com/emma-simbot/experience-hub/compare/v1.7.4...v1.8.0) (2022-10-20)


### Features

* send the done dialog action when the stop token is decoded ([#101](https://github.com/emma-simbot/experience-hub/issues/101)) ([37ae9fb](https://github.com/emma-simbot/experience-hub/commit/37ae9fb4c02b0dcddbfd46b201024bca4015b084))


### Bug Fixes

* move when action ids are updated to the end of the pipeline ([33fd981](https://github.com/emma-simbot/experience-hub/commit/33fd981deb66b8d44c96287e6747e4d1bef7c5b0))
* provide the simbot id to action returned by the press button intent ([ade93ba](https://github.com/emma-simbot/experience-hub/commit/ade93bad19985f84680e90c0078d47e2eda084ac))
* watchtower logging ([f4d4963](https://github.com/emma-simbot/experience-hub/commit/f4d4963ebb83e6fbff807670bf2bccff199a4f7a))

## [1.7.4](https://github.com/emma-simbot/experience-hub/compare/v1.7.3...v1.7.4) (2022-10-19)


### Bug Fixes

* param error to set server endpoint for placeholder vision client ([da2deb8](https://github.com/emma-simbot/experience-hub/commit/da2deb8afb876c05f378489796fc947fc983b2f2))

## [1.7.3](https://github.com/emma-simbot/experience-hub/compare/v1.7.2...v1.7.3) (2022-10-18)


### Bug Fixes

* use `OBJECT_MASK` for Goto action by default ([#108](https://github.com/emma-simbot/experience-hub/issues/108)) ([dde8f52](https://github.com/emma-simbot/experience-hub/commit/dde8f529cb609ce745fc59e24e35a5c5a283c89a))

## [1.7.2](https://github.com/emma-simbot/experience-hub/compare/v1.7.1...v1.7.2) (2022-10-18)


### Bug Fixes

* include the new action error type ([#107](https://github.com/emma-simbot/experience-hub/issues/107)) ([f22fb7d](https://github.com/emma-simbot/experience-hub/commit/f22fb7d566f2ea6193dacdd73cfe8d9ec1f925f1))

## [1.7.1](https://github.com/emma-simbot/experience-hub/compare/v1.7.0...v1.7.1) (2022-10-18)


### Bug Fixes

* use threadpool for validating the features have been extracted for a given session ([#105](https://github.com/emma-simbot/experience-hub/issues/105)) ([f875f90](https://github.com/emma-simbot/experience-hub/commit/f875f9030969a573acbd705e21ad0dca19ef1a6e))

## [1.7.0](https://github.com/emma-simbot/experience-hub/compare/v1.6.1...v1.7.0) (2022-10-17)


### Features

* integrate a client to get the button mask from the placeholder vision model ([#103](https://github.com/emma-simbot/experience-hub/issues/103)) ([248b099](https://github.com/emma-simbot/experience-hub/commit/248b0992e145eb533b21d5ff736d4277ea40440d))

## [1.6.1](https://github.com/emma-simbot/experience-hub/compare/v1.6.0...v1.6.1) (2022-10-14)


### Bug Fixes

* lower the asr average threshold to 0.55 (from 0.6) ([#98](https://github.com/emma-simbot/experience-hub/issues/98)) ([519bd03](https://github.com/emma-simbot/experience-hub/commit/519bd039559243b947de549e225de2a8fd6a57ec))
* stop action parsing error from preventing actions when both special tokens exist ([#97](https://github.com/emma-simbot/experience-hub/issues/97)) ([70944f0](https://github.com/emma-simbot/experience-hub/commit/70944f09118cbddf3a8201d2e2b76b03fd985982))

## [1.6.0](https://github.com/emma-simbot/experience-hub/compare/v1.5.0...v1.6.0) (2022-10-14)


### Features

* added support for turnaround action in parser ([#96](https://github.com/emma-simbot/experience-hub/issues/96)) ([8e28185](https://github.com/emma-simbot/experience-hub/commit/8e28185888e2f0f433a8550ea17aea632d3b0134))

## [1.5.0](https://github.com/emma-simbot/experience-hub/compare/v1.4.1...v1.5.0) (2022-10-14)


### Features

* filter Alexa wake words from the processed utterance ([#95](https://github.com/emma-simbot/experience-hub/issues/95)) ([202ffea](https://github.com/emma-simbot/experience-hub/commit/202ffea89d20b7c49eb761fea0a941bb6ba5616c))

## [1.4.1](https://github.com/emma-simbot/experience-hub/compare/v1.4.0...v1.4.1) (2022-10-14)


### Bug Fixes

* increase the default ASR average confidence threshold ([#94](https://github.com/emma-simbot/experience-hub/issues/94)) ([1a1d6a2](https://github.com/emma-simbot/experience-hub/commit/1a1d6a2fb74dd9284ef16e07ee0c72929060868e))

## [1.4.0](https://github.com/emma-simbot/experience-hub/compare/v1.3.1...v1.4.0) (2022-10-14)


### Features

* Get object mask from frame vis tokens ([#85](https://github.com/emma-simbot/experience-hub/issues/85)) ([5362492](https://github.com/emma-simbot/experience-hub/commit/5362492357fb0c8395c2e11325760b2fe4271d62))

## [1.3.1](https://github.com/emma-simbot/experience-hub/compare/v1.3.0...v1.3.1) (2022-10-14)


### Bug Fixes

* providing correct turns after non-actionable utterances  ([#92](https://github.com/emma-simbot/experience-hub/issues/92)) ([a13bffd](https://github.com/emma-simbot/experience-hub/commit/a13bffdf64eef02a7cb98549ce6dd61612b95044))

## [1.3.0](https://github.com/emma-simbot/experience-hub/compare/v1.2.4...v1.3.0) (2022-10-13)


### Features

* make it easier to launch the simbot API from a single command ([#87](https://github.com/emma-simbot/experience-hub/issues/87)) ([a5d37d3](https://github.com/emma-simbot/experience-hub/commit/a5d37d37f1b9039aab9bd89f8b8280f3df357485))

## [1.2.4](https://github.com/emma-simbot/experience-hub/compare/v1.2.3...v1.2.4) (2022-10-13)


### Bug Fixes

* only send current turn for intent extraction ([#83](https://github.com/emma-simbot/experience-hub/issues/83)) ([11cee06](https://github.com/emma-simbot/experience-hub/commit/11cee06df811465a550f4c43fae03156493aea76))

## [1.2.3](https://github.com/emma-simbot/experience-hub/compare/v1.2.2...v1.2.3) (2022-10-13)


### Bug Fixes

* **docker:** command for running the out of domain detector ([#88](https://github.com/emma-simbot/experience-hub/issues/88)) ([11ff582](https://github.com/emma-simbot/experience-hub/commit/11ff5820f24150f9e6ab5965b648a71be1edc27b))

## [1.2.2](https://github.com/emma-simbot/experience-hub/compare/v1.2.1...v1.2.2) (2022-10-13)


### Bug Fixes

* logging properly (with and without api) ([#86](https://github.com/emma-simbot/experience-hub/issues/86)) ([021b2de](https://github.com/emma-simbot/experience-hub/commit/021b2dea2a8ee05cdfed7f02757c374fdf5c90f4))

## [1.2.1](https://github.com/emma-simbot/experience-hub/compare/v1.2.0...v1.2.1) (2022-10-13)


### Bug Fixes

* endpoint for out of domain detector ([#84](https://github.com/emma-simbot/experience-hub/issues/84)) ([f1ade36](https://github.com/emma-simbot/experience-hub/commit/f1ade36d89883e92f4f8c3aea567249fd82e7cbf))

## [1.2.0](https://github.com/emma-simbot/experience-hub/compare/v1.1.2...v1.2.0) (2022-10-13)


### Features

* filter utterances when the average confidence of the ASR output is below a threshold ([#82](https://github.com/emma-simbot/experience-hub/issues/82)) ([6af6aaf](https://github.com/emma-simbot/experience-hub/commit/6af6aafba9e6bfd3e11da3a9e29c384e925df7f2))

## [1.1.2](https://github.com/emma-simbot/experience-hub/compare/v1.1.1...v1.1.2) (2022-10-13)


### Bug Fixes

* provide emma services with the correct turns as history ([#79](https://github.com/emma-simbot/experience-hub/issues/79)) ([875eca6](https://github.com/emma-simbot/experience-hub/commit/875eca6d60abbdd07029643f7286aba3bcbdd4c8))

## [1.1.1](https://github.com/emma-simbot/experience-hub/compare/v1.1.0...v1.1.1) (2022-10-13)


### Bug Fixes

* Provide num frames in current turn ([#80](https://github.com/emma-simbot/experience-hub/issues/80)) ([1cdd264](https://github.com/emma-simbot/experience-hub/commit/1cdd26488ee8fad20b79824808b1e2fd1f91adc5))

## [1.1.0](https://github.com/emma-simbot/experience-hub/compare/v1.0.0...v1.1.0) (2022-10-12)


### Features

* integrate OOD detection as a service ([#77](https://github.com/emma-simbot/experience-hub/issues/77)) ([0050c72](https://github.com/emma-simbot/experience-hub/commit/0050c72ff1fae99e8532ebee571f46a2e5d8d8f3))

## 1.0.0 (2022-10-12)


### Features

* add editorconfig ([9b270f6](https://github.com/emma-simbot/experience-hub/commit/9b270f6751bdb5789ab41f6eacf3d8d6d1be1853))
* **release:** automate package releasing when new changes are added to `main` ([#76](https://github.com/emma-simbot/experience-hub/issues/76)) ([389c834](https://github.com/emma-simbot/experience-hub/commit/389c8349672aed7cc34bf0a90081a0e4df3e3742))
