# Changelog

All notable changes to this project will be documented in this file. See
[Conventional Commits](https://conventionalcommits.org) for commit guidelines.

## [7.10.0](https://github.com/emma-simbot/experience-hub/compare/v7.9.1...v7.10.0) (2023-02-14)


### Features

* include the new `simbot-hacks` client with the raw text matching ([#316](https://github.com/emma-simbot/experience-hub/issues/316)) ([58893bd](https://github.com/emma-simbot/experience-hub/commit/58893bd977ca1f01561b7aed0369e1612d4a28cc))


### Bug Fixes

* Ignore environment errors when we get a new user utterance ([#348](https://github.com/emma-simbot/experience-hub/issues/348)) ([6f4ad7e](https://github.com/emma-simbot/experience-hub/commit/6f4ad7e5b0599c9178f39e2bf6b578c26b5cf972))

## [7.9.1](https://github.com/emma-simbot/experience-hub/compare/v7.9.0...v7.9.1) (2023-02-14)


### Bug Fixes

* lightweight feedback state ([#344](https://github.com/emma-simbot/experience-hub/issues/344)) ([f38e07a](https://github.com/emma-simbot/experience-hub/commit/f38e07a9015873df988a9bd5f8342ec9ca9b7139))

## [7.9.0](https://github.com/emma-simbot/experience-hub/compare/v7.8.1...v7.9.0) (2023-02-13)


### Features

* Update confirmation classifier repo version to 1.3.0 and s3 endpoint ([#345](https://github.com/emma-simbot/experience-hub/issues/345)) ([fdc05e2](https://github.com/emma-simbot/experience-hub/commit/fdc05e234d80f7963bd97b5ed5df6f050c71ef80))

## [7.8.1](https://github.com/emma-simbot/experience-hub/compare/v7.8.0...v7.8.1) (2023-02-12)


### Bug Fixes

* revert confirmation classifier registry changes ([ca2c243](https://github.com/emma-simbot/experience-hub/commit/ca2c2438735d163b32bdb75165116179e516588f))

## [7.8.0](https://github.com/emma-simbot/experience-hub/compare/v7.7.0...v7.8.0) (2023-02-11)


### Features

* new ood model ([#341](https://github.com/emma-simbot/experience-hub/issues/341)) ([a7cee45](https://github.com/emma-simbot/experience-hub/commit/a7cee45c3d80386ed92c65e2fcc099aeb159c0c6))

## [7.7.0](https://github.com/emma-simbot/experience-hub/compare/v7.6.1...v7.7.0) (2023-02-10)


### Features

* Confirmation Classifier Registry Changes ([#340](https://github.com/emma-simbot/experience-hub/issues/340)) ([afe95e8](https://github.com/emma-simbot/experience-hub/commit/afe95e84cdaa2c0ceefd45a06376d2280020b57a))

## [7.6.1](https://github.com/emma-simbot/experience-hub/compare/v7.6.0...v7.6.1) (2023-02-10)


### Bug Fixes

* include-found-object-in-response ([#338](https://github.com/emma-simbot/experience-hub/issues/338)) ([b7e02df](https://github.com/emma-simbot/experience-hub/commit/b7e02df413e1851f16fc177907476b05f040e280))

## [7.6.0](https://github.com/emma-simbot/experience-hub/compare/v7.5.0...v7.6.0) (2023-02-10)


### Features

* bump policy to 1.26.0 ([#339](https://github.com/emma-simbot/experience-hub/issues/339)) ([f419066](https://github.com/emma-simbot/experience-hub/commit/f419066f4816d17815a1faf6fe77972e375a216c))


### Bug Fixes

* synonym casing matching with language ([#336](https://github.com/emma-simbot/experience-hub/issues/336)) ([f75d6e2](https://github.com/emma-simbot/experience-hub/commit/f75d6e2a618ef32bdda2c147abd03f57ec7ca37c))

## [7.5.0](https://github.com/emma-simbot/experience-hub/compare/v7.4.0...v7.5.0) (2023-02-10)


### Features

* add responses for `verbal_interaction_intent_entity` with `act_no_match` intent ([#337](https://github.com/emma-simbot/experience-hub/issues/337)) ([28be9af](https://github.com/emma-simbot/experience-hub/commit/28be9af702f5af9b87a394afebb5f7e13a430ef2))

## [7.4.0](https://github.com/emma-simbot/experience-hub/compare/v7.3.0...v7.4.0) (2023-02-10)


### Features

* loosen conditions in feedback rules ([#330](https://github.com/emma-simbot/experience-hub/issues/330)) ([1b606a1](https://github.com/emma-simbot/experience-hub/commit/1b606a199ece738366c39f41022875b05ad1e967))

## [7.3.0](https://github.com/emma-simbot/experience-hub/compare/v7.2.1...v7.3.0) (2023-02-10)


### Features

* always cache the auxiliary metadata for the current turn ([#335](https://github.com/emma-simbot/experience-hub/issues/335)) ([4768f27](https://github.com/emma-simbot/experience-hub/commit/4768f27cca522a23bb228a3e0642280fdb797f11))

## [7.2.1](https://github.com/emma-simbot/experience-hub/compare/v7.2.0...v7.2.1) (2023-02-08)


### Bug Fixes

* remove simbot settings from being a global ([8e5473d](https://github.com/emma-simbot/experience-hub/commit/8e5473df158c89a14d49f1336a98d503e2342077))

## [7.2.0](https://github.com/emma-simbot/experience-hub/compare/v7.1.1...v7.2.0) (2023-02-08)


### Features

* Disable search after no match ([#327](https://github.com/emma-simbot/experience-hub/issues/327)) ([c463bfb](https://github.com/emma-simbot/experience-hub/commit/c463bfb8d38f8c8c3f2b225ae9181d1987bd0b86))

## [7.1.1](https://github.com/emma-simbot/experience-hub/compare/v7.1.0...v7.1.1) (2023-02-07)


### Bug Fixes

* Avoid infinite search-no match loop by forcing act_one_match ([#324](https://github.com/emma-simbot/experience-hub/issues/324)) ([6b333cb](https://github.com/emma-simbot/experience-hub/commit/6b333cb53237f86f14b0963dc76ecf61e9effa5d))

## [7.1.0](https://github.com/emma-simbot/experience-hub/compare/v7.0.0...v7.1.0) (2023-02-07)


### Features

* act_no_match to search pipeline ([#317](https://github.com/emma-simbot/experience-hub/issues/317)) ([fb23bc1](https://github.com/emma-simbot/experience-hub/commit/fb23bc151e941e455a4c4886116075b670395dfa))

## [7.0.0](https://github.com/emma-simbot/experience-hub/compare/v6.17.0...v7.0.0) (2023-02-02)


### ⚠ BREAKING CHANGES

* split `agent`  intent into `physical_interaction` and `verbal_interaction` (#297)

### Features

* split `agent`  intent into `physical_interaction` and `verbal_interaction` ([#297](https://github.com/emma-simbot/experience-hub/issues/297)) ([423192f](https://github.com/emma-simbot/experience-hub/commit/423192f3eb55cd401ff0957e0d4b8f4a5407f04a))
* Update the OOD model ([#312](https://github.com/emma-simbot/experience-hub/issues/312)) ([e5d3ca1](https://github.com/emma-simbot/experience-hub/commit/e5d3ca1f2872e497d661df13889f221b31790a97))

## [6.17.0](https://github.com/emma-simbot/experience-hub/compare/v6.16.0...v6.17.0) (2023-02-02)


### Features

* Add holding object to each turn ([#310](https://github.com/emma-simbot/experience-hub/issues/310)) ([615fa01](https://github.com/emma-simbot/experience-hub/commit/615fa018e18fa479631ddfa5c443a4854c674533)), closes [#307](https://github.com/emma-simbot/experience-hub/issues/307)

## [6.16.0](https://github.com/emma-simbot/experience-hub/compare/v6.15.0...v6.16.0) (2023-02-02)


### Features

* add a debug mode which will always highlight the object before performing the action ([#298](https://github.com/emma-simbot/experience-hub/issues/298)) ([5595c54](https://github.com/emma-simbot/experience-hub/commit/5595c5414dc904e7e7bc312ea2621aae64a3c512))

## [6.15.0](https://github.com/emma-simbot/experience-hub/compare/v6.14.0...v6.15.0) (2023-02-01)


### Features

* ensure every action from the previous turn has a status ([#306](https://github.com/emma-simbot/experience-hub/issues/306)) ([1f3eca1](https://github.com/emma-simbot/experience-hub/commit/1f3eca1335257e544640876ad3a90d8d86c1f497))


### Reverts

* simbot models ([#304](https://github.com/emma-simbot/experience-hub/issues/304)) ([1094700](https://github.com/emma-simbot/experience-hub/commit/109470075a7cb70359fe11c16a5e97e1ad54f93c))

## [6.14.0](https://github.com/emma-simbot/experience-hub/compare/v6.13.0...v6.14.0) (2023-01-30)


### Features

* Update action, nlu models, and policy version ([#303](https://github.com/emma-simbot/experience-hub/issues/303)) ([031fb8b](https://github.com/emma-simbot/experience-hub/commit/031fb8b46c0f76513dcfc5a888532d159b41bb0c))


### Bug Fixes

* formatting and update pre-commit config ([e308cef](https://github.com/emma-simbot/experience-hub/commit/e308cef7ed934535dc48739126f20189c587d23b))

## [6.13.0](https://github.com/emma-simbot/experience-hub/compare/v6.12.0...v6.13.0) (2023-01-27)


### Features

* Check 2 viewpoints and add more search responses ([#296](https://github.com/emma-simbot/experience-hub/issues/296)) ([54c8dab](https://github.com/emma-simbot/experience-hub/commit/54c8dab75c9a0b4d790c69081b76ef93a7c0a706))

## [6.12.0](https://github.com/emma-simbot/experience-hub/compare/v6.11.0...v6.12.0) (2023-01-27)


### Features

* choose a rule from the bin of highest scoring rules with the same score ([#292](https://github.com/emma-simbot/experience-hub/issues/292)) ([913baff](https://github.com/emma-simbot/experience-hub/commit/913baff266ea69153413e90565076900efc37a1a))


### Bug Fixes

* add a default rule for the lightweight dialog ([#295](https://github.com/emma-simbot/experience-hub/issues/295)) ([7a6353d](https://github.com/emma-simbot/experience-hub/commit/7a6353d9679ec7ae616336d5c075efad4c18a449)), closes [#271](https://github.com/emma-simbot/experience-hub/issues/271)

## [6.11.0](https://github.com/emma-simbot/experience-hub/compare/v6.10.0...v6.11.0) (2023-01-26)


### Features

* support detecting answers to confirmation questions ([#291](https://github.com/emma-simbot/experience-hub/issues/291)) ([d2afaeb](https://github.com/emma-simbot/experience-hub/commit/d2afaeb8522dabae35e21144caeaa51a50de6213))

## [6.10.0](https://github.com/emma-simbot/experience-hub/compare/v6.9.1...v6.10.0) (2023-01-26)


### Features

* Include class labels in features ([#288](https://github.com/emma-simbot/experience-hub/issues/288)) ([5dbb66f](https://github.com/emma-simbot/experience-hub/commit/5dbb66fa2b438cee9f0b5fa5058365d94b7610a3))

## [6.9.1](https://github.com/emma-simbot/experience-hub/compare/v6.9.0...v6.9.1) (2023-01-25)


### Bug Fixes

* prefix watchtower logstreams with the service name ([8126288](https://github.com/emma-simbot/experience-hub/commit/812628870b43718bb32c8123f346eb25383741c2))

## [6.9.0](https://github.com/emma-simbot/experience-hub/compare/v6.8.2...v6.9.0) (2023-01-25)


### Features

* Update simbot models ([#287](https://github.com/emma-simbot/experience-hub/issues/287)) ([90b3c6b](https://github.com/emma-simbot/experience-hub/commit/90b3c6be22c3179a547495c127bb394cebf01312))

## [6.8.2](https://github.com/emma-simbot/experience-hub/compare/v6.8.1...v6.8.2) (2023-01-24)


### Bug Fixes

* need to create the directory for the file before writing to it ([8a8c4c3](https://github.com/emma-simbot/experience-hub/commit/8a8c4c34e84c4159b34eff16f4b369e776bea258))

## [6.8.1](https://github.com/emma-simbot/experience-hub/compare/v6.8.0...v6.8.1) (2023-01-24)


### Bug Fixes

* **cli:** explicitly add params when calling typer-wrapped functions ([2de282c](https://github.com/emma-simbot/experience-hub/commit/2de282c1364ba255dd93d13bff844c524c4c2704))

## [6.8.0](https://github.com/emma-simbot/experience-hub/compare/v6.7.2...v6.8.0) (2023-01-23)


### Features

* refactor cache clients to only upload to S3 after API response ([#282](https://github.com/emma-simbot/experience-hub/issues/282)) ([031e05a](https://github.com/emma-simbot/experience-hub/commit/031e05a52d47f83613775f2e323c9bd75d73a668))

## [6.7.2](https://github.com/emma-simbot/experience-hub/compare/v6.7.1...v6.7.2) (2023-01-23)


### Bug Fixes

* Bug in selecting search viewpoints ([#281](https://github.com/emma-simbot/experience-hub/issues/281)) ([fa81a10](https://github.com/emma-simbot/experience-hub/commit/fa81a1029fa449b60a04af873d3ff5e243c325b7))

## [6.7.1](https://github.com/emma-simbot/experience-hub/compare/v6.7.0...v6.7.1) (2023-01-23)


### Bug Fixes

* Enable search across viewpoints and reset of utterance queue ([#263](https://github.com/emma-simbot/experience-hub/issues/263)) ([4936421](https://github.com/emma-simbot/experience-hub/commit/4936421302a2d9b8f66c28c4a0a873eb6d651978))

## [6.7.0](https://github.com/emma-simbot/experience-hub/compare/v6.6.3...v6.7.0) (2023-01-20)


### Features

* customise timeouts for all the clients from the settings ([#277](https://github.com/emma-simbot/experience-hub/issues/277)) ([c5330db](https://github.com/emma-simbot/experience-hub/commit/c5330dbcac60301685933e69fc76d3ac97c9a2e4))


### Bug Fixes

* added instructions to run EMMA on staging ([#275](https://github.com/emma-simbot/experience-hub/issues/275)) ([76ac2fd](https://github.com/emma-simbot/experience-hub/commit/76ac2fd2680e4236748c243881c13c96be201670))

## [6.6.3](https://github.com/emma-simbot/experience-hub/compare/v6.6.2...v6.6.3) (2023-01-20)


### Bug Fixes

* **cli:** add option to change the model storage dir ([6f72952](https://github.com/emma-simbot/experience-hub/commit/6f7295208ad17ca2ff453c3a9ae9dc9fccc83803))

## [6.6.2](https://github.com/emma-simbot/experience-hub/compare/v6.6.1...v6.6.2) (2023-01-20)


### Bug Fixes

* add `<stop>` token in last turn left in the look around ([45db0ed](https://github.com/emma-simbot/experience-hub/commit/45db0ed466e909f526a7e515261febe4be8446d4))

## [6.6.1](https://github.com/emma-simbot/experience-hub/compare/v6.6.0...v6.6.1) (2023-01-19)


### Bug Fixes

* missing rule for lightweight dialogue when policy hasn't finished generating ([#271](https://github.com/emma-simbot/experience-hub/issues/271)) ([4618858](https://github.com/emma-simbot/experience-hub/commit/46188587aa49e368998a8e1dd505b80df0a5094a))

## [6.6.0](https://github.com/emma-simbot/experience-hub/compare/v6.5.0...v6.6.0) (2023-01-19)


### Features

* Update ood detection model ([#274](https://github.com/emma-simbot/experience-hub/issues/274)) ([5321f6c](https://github.com/emma-simbot/experience-hub/commit/5321f6c28ba231c60619afc06fe33e720d10438f))

## [6.5.0](https://github.com/emma-simbot/experience-hub/compare/v6.4.1...v6.5.0) (2023-01-19)


### Features

* build a search plan if we find the entity in the history (GFH) ([#264](https://github.com/emma-simbot/experience-hub/issues/264)) ([ad70e7b](https://github.com/emma-simbot/experience-hub/commit/ad70e7b997c86211dc2c903d86e759d64886ccf4)), closes [#229](https://github.com/emma-simbot/experience-hub/issues/229)

## [6.4.1](https://github.com/emma-simbot/experience-hub/compare/v6.4.0...v6.4.1) (2023-01-18)


### Bug Fixes

* do not send the agent utterances to the visual grounding endpoint ([#266](https://github.com/emma-simbot/experience-hub/issues/266)) ([a2946b5](https://github.com/emma-simbot/experience-hub/commit/a2946b5314dd37bff9d45a65d3e63e876b0a94d9))

## [6.4.0](https://github.com/emma-simbot/experience-hub/compare/v6.3.10...v6.4.0) (2023-01-17)


### Features

* add feedback for `only_wake_word` and `empty_utterance` intents ([#260](https://github.com/emma-simbot/experience-hub/issues/260)) ([397cc8d](https://github.com/emma-simbot/experience-hub/commit/397cc8de84a2bb2a1427ce7d0f9983f33b74ade0))

## [6.3.10](https://github.com/emma-simbot/experience-hub/compare/v6.3.9...v6.3.10) (2023-01-13)


### Bug Fixes

* disable timeout when extracting features ([#261](https://github.com/emma-simbot/experience-hub/issues/261)) ([acdd96b](https://github.com/emma-simbot/experience-hub/commit/acdd96b30b2a1b66e4ddb613d86bc668ca79d66c))

## [6.3.9](https://github.com/emma-simbot/experience-hub/compare/v6.3.8...v6.3.9) (2023-01-12)


### Bug Fixes

* messy docker compose configs ([30b4357](https://github.com/emma-simbot/experience-hub/commit/30b4357a90b9dcd711b113b5c865e2255d9fab16))

## [6.3.8](https://github.com/emma-simbot/experience-hub/compare/v6.3.7...v6.3.8) (2023-01-11)


### Bug Fixes

* bump compound splitter image version ([8d5038c](https://github.com/emma-simbot/experience-hub/commit/8d5038c171c49c3d4aa1dca6f37c3bb807535d1b))

## [6.3.7](https://github.com/emma-simbot/experience-hub/compare/v6.3.6...v6.3.7) (2023-01-11)


### Bug Fixes

* bump confirmation classifier to 1.1.0 ([50028b6](https://github.com/emma-simbot/experience-hub/commit/50028b6b1bd19ab09cad25b5b92b1753f70a8b29))

## [6.3.6](https://github.com/emma-simbot/experience-hub/compare/v6.3.5...v6.3.6) (2023-01-11)


### Bug Fixes

* bump the confirmation classifier value down to 1.0.0 ([38cb180](https://github.com/emma-simbot/experience-hub/commit/38cb18056f8e65a7e38f88b70b5600e9fc0d0490))

## [6.3.5](https://github.com/emma-simbot/experience-hub/compare/v6.3.4...v6.3.5) (2023-01-11)


### Bug Fixes

* bump policy image version in registry ([5e31414](https://github.com/emma-simbot/experience-hub/commit/5e314142ffd2a80ee38f063dd60617636a72089a))

## [6.3.4](https://github.com/emma-simbot/experience-hub/compare/v6.3.3...v6.3.4) (2023-01-11)


### Bug Fixes

* docker run command needs to be right ([1e7d055](https://github.com/emma-simbot/experience-hub/commit/1e7d055320309d5f50d3605da0b4c7f8000a8915))

## [6.3.3](https://github.com/emma-simbot/experience-hub/compare/v6.3.2...v6.3.3) (2023-01-11)


### Bug Fixes

* docker compose config for different environments ([2beca0c](https://github.com/emma-simbot/experience-hub/commit/2beca0c5c0725fa0f311872669f60eaab1cad7fb))
* remove the compose file merging when trying to run background services ([3fcd468](https://github.com/emma-simbot/experience-hub/commit/3fcd468236d9eb7944193a1ffd5dff610175ce75))

## [6.3.2](https://github.com/emma-simbot/experience-hub/compare/v6.3.1...v6.3.2) (2023-01-11)


### Bug Fixes

* Response generation for first turn and search when no object was found ([#257](https://github.com/emma-simbot/experience-hub/issues/257)) ([8e4639c](https://github.com/emma-simbot/experience-hub/commit/8e4639c5bfacfc5c984372caeddc0b5f7ce0db5d))

## [6.3.1](https://github.com/emma-simbot/experience-hub/compare/v6.3.0...v6.3.1) (2023-01-11)


### Bug Fixes

* the `>` character needs to be in the raw output field ([79c519e](https://github.com/emma-simbot/experience-hub/commit/79c519ecee0792257de35c596b3d2469fb7d03c9))

## [6.3.0](https://github.com/emma-simbot/experience-hub/compare/v6.2.0...v6.3.0) (2023-01-10)


### Features

* Enable clarifications ([#256](https://github.com/emma-simbot/experience-hub/issues/256)) ([e423de2](https://github.com/emma-simbot/experience-hub/commit/e423de279a254054837dc05309fdb70b9006e7b7))

## [6.2.0](https://github.com/emma-simbot/experience-hub/compare/v6.1.1...v6.2.0) (2023-01-10)


### Features

* bump service registry versions for perception and confirmation-classifier ([2751f98](https://github.com/emma-simbot/experience-hub/commit/2751f983f8a7753b5a2e275b9fa2f43a22c7e09d))

## [6.1.1](https://github.com/emma-simbot/experience-hub/compare/v6.1.0...v6.1.1) (2023-01-09)


### Bug Fixes

* only generate lightweight dialogs when model does not return end of trajectory token ([#254](https://github.com/emma-simbot/experience-hub/issues/254)) ([f0afa66](https://github.com/emma-simbot/experience-hub/commit/f0afa6658c3bc5422f266784636fbd94070ecf67))

## [6.1.0](https://github.com/emma-simbot/experience-hub/compare/v6.0.1...v6.1.0) (2023-01-06)


### Features

* bump policy to 1.14.1 ([#253](https://github.com/emma-simbot/experience-hub/issues/253)) ([1d09d2a](https://github.com/emma-simbot/experience-hub/commit/1d09d2a47bcf1aa9cdb6eb81138b07a415fa1c86))

## [6.0.1](https://github.com/emma-simbot/experience-hub/compare/v6.0.0...v6.0.1) (2023-01-06)


### Bug Fixes

* Make four rotate left actions in the basic planner ([#249](https://github.com/emma-simbot/experience-hub/issues/249)) ([f700d6c](https://github.com/emma-simbot/experience-hub/commit/f700d6c6b799d95efaf669df0bcea1837578d673))

## [6.0.0](https://github.com/emma-simbot/experience-hub/compare/v5.39.1...v6.0.0) (2023-01-05)


### ⚠ BREAKING CHANGES

* use grammar-style parsing to generate responses (#245)

### Features

* use grammar-style parsing to generate responses ([#245](https://github.com/emma-simbot/experience-hub/issues/245)) ([0879895](https://github.com/emma-simbot/experience-hub/commit/087989549ce33e5e48176ff62c4cfc237d586939))

## [5.39.1](https://github.com/emma-simbot/experience-hub/compare/v5.39.0...v5.39.1) (2023-01-05)


### Bug Fixes

* **api:** return 500 if the api is not healthy ([3e1befc](https://github.com/emma-simbot/experience-hub/commit/3e1befcaf01030bb4f205cf334dc08ad331f28fe))

## [5.39.0](https://github.com/emma-simbot/experience-hub/compare/v5.38.0...v5.39.0) (2023-01-02)


### Features

* **simbot/cli:** add command to pull all related service images ([5c0698b](https://github.com/emma-simbot/experience-hub/commit/5c0698bf39f532fc6da0ac36be8e70002bb55280))
* **telemetry:** improve trace metadata and send metrics to opensearch ([c7dc1b5](https://github.com/emma-simbot/experience-hub/commit/c7dc1b5f80b26fcd84c435b0ded15312f4adef29))


### Bug Fixes

* **deps:** fix poetry.lock file ([3178a74](https://github.com/emma-simbot/experience-hub/commit/3178a749db6607bd0e51179efb10c92188c6e219))
* **telemetry:** stop tracking healthcheck calls ([250a363](https://github.com/emma-simbot/experience-hub/commit/250a363a0175ad0f6d0dac02f4bbfa8e5edc3b25))

## [5.38.0](https://github.com/emma-simbot/experience-hub/compare/v5.37.0...v5.38.0) (2022-12-31)


### Features

* **telemetry:** add tracing when getting auxiliary metadata ([a4863ca](https://github.com/emma-simbot/experience-hub/commit/a4863ca55fffca07522b02e5c257b3c0d345a7c1))

## [5.37.0](https://github.com/emma-simbot/experience-hub/compare/v5.36.0...v5.37.0) (2022-12-25)


### Features

* **telemetry:** add tracing within the "build environment state history" ([6fd4376](https://github.com/emma-simbot/experience-hub/commit/6fd4376193f6e8bc833d17c7ceac80e2227898a0))

## [5.36.0](https://github.com/emma-simbot/experience-hub/compare/v5.35.0...v5.36.0) (2022-12-24)


### Features

* optimise the compress segmentation mask function further ([#240](https://github.com/emma-simbot/experience-hub/issues/240)) ([f8ca410](https://github.com/emma-simbot/experience-hub/commit/f8ca410fab4f426171aef3a6ffa2c20b3bae508a)), closes [#239](https://github.com/emma-simbot/experience-hub/issues/239)
* **telemetry:** monitor steps before prediction action with emma policy ([5691a8d](https://github.com/emma-simbot/experience-hub/commit/5691a8d949ad339cfbe10c59ca09b79a8d0ebac2))

## [5.35.0](https://github.com/emma-simbot/experience-hub/compare/v5.34.0...v5.35.0) (2022-12-24)


### Features

* **telemetry:** trace the compress segmentation mask fn ([256ea2e](https://github.com/emma-simbot/experience-hub/commit/256ea2e064606bb9662c40a3f3d551084020b492))


### Bug Fixes

* optimise creating actions for the found object to only extract the mask once ([b51ee94](https://github.com/emma-simbot/experience-hub/commit/b51ee9493b0662c73ba8fd41aa1a60f4eadc5bcd))

## [5.34.0](https://github.com/emma-simbot/experience-hub/compare/v5.33.0...v5.34.0) (2022-12-23)


### Features

* enable tracing on perception and policy services ([#235](https://github.com/emma-simbot/experience-hub/issues/235)) ([56f9d0b](https://github.com/emma-simbot/experience-hub/commit/56f9d0be4c39e62213f08bd8ef38ce298bbc7946))

## [5.33.0](https://github.com/emma-simbot/experience-hub/compare/v5.32.2...v5.33.0) (2022-12-23)


### Features

* add more tracing to various pipelines ([#238](https://github.com/emma-simbot/experience-hub/issues/238)) ([b499c47](https://github.com/emma-simbot/experience-hub/commit/b499c47242b58bb656788f3554c6ffebf47f124a))


### Bug Fixes

* optimise the compress segmentation mask fn ([#239](https://github.com/emma-simbot/experience-hub/issues/239)) ([070a0c2](https://github.com/emma-simbot/experience-hub/commit/070a0c272ba315448077772828d06410ea1449c8))

## [5.32.2](https://github.com/emma-simbot/experience-hub/compare/v5.32.1...v5.32.2) (2022-12-23)


### Bug Fixes

* bump emma-common dep ([9c3723f](https://github.com/emma-simbot/experience-hub/commit/9c3723fc89cf25bdf1ecd671c857ace325a3e627))
* **registry:** bump ood ([88e763b](https://github.com/emma-simbot/experience-hub/commit/88e763b80a982765f96823bab9b3e792f314f0c4))

## [5.32.1](https://github.com/emma-simbot/experience-hub/compare/v5.32.0...v5.32.1) (2022-12-22)


### Bug Fixes

* re-enable the compound splitter ([#225](https://github.com/emma-simbot/experience-hub/issues/225)) ([02825cf](https://github.com/emma-simbot/experience-hub/commit/02825cf9cddb83a7fc9a1b8e7151712fa2c7487e))

## [5.32.0](https://github.com/emma-simbot/experience-hub/compare/v5.31.1...v5.32.0) (2022-12-21)


### Features

* run neural services on separate GPUs ([#237](https://github.com/emma-simbot/experience-hub/issues/237)) ([4b1d54b](https://github.com/emma-simbot/experience-hub/commit/4b1d54b7263b9e97d8b2d25fe5e7049d1e560648))

## [5.31.1](https://github.com/emma-simbot/experience-hub/compare/v5.31.0...v5.31.1) (2022-12-20)


### Bug Fixes

* tracing through services and clients ([#234](https://github.com/emma-simbot/experience-hub/issues/234)) ([58fc563](https://github.com/emma-simbot/experience-hub/commit/58fc56307491164dcacbf12fef7933c7cdc2f3f7))

## [5.31.0](https://github.com/emma-simbot/experience-hub/compare/v5.30.0...v5.31.0) (2022-12-20)


### Features

* add flag to enable/disable observability for background services ([#233](https://github.com/emma-simbot/experience-hub/issues/233)) ([16a64e1](https://github.com/emma-simbot/experience-hub/commit/16a64e1b79c1d8859cf96092c78808aa09385daf))

## [5.30.0](https://github.com/emma-simbot/experience-hub/compare/v5.29.4...v5.30.0) (2022-12-19)


### Features

* **services:** integrate tracing across services with OOD ([#231](https://github.com/emma-simbot/experience-hub/issues/231)) ([b648ef4](https://github.com/emma-simbot/experience-hub/commit/b648ef49654fe13d6920db7c60b976992b68f994))


### Bug Fixes

* imports with emma-common ([164d5eb](https://github.com/emma-simbot/experience-hub/commit/164d5eb51f412ffdb048a6eaa613b43728112f0d))

## [5.29.4](https://github.com/emma-simbot/experience-hub/compare/v5.29.3...v5.29.4) (2022-12-17)


### Bug Fixes

* instrumentations with emma-common@^1.13.0 ([931c5b4](https://github.com/emma-simbot/experience-hub/commit/931c5b46c21e1b6360996056545cd2bd42d7729b))
* sort session turns by idx instead of timestamps ([1e17cf6](https://github.com/emma-simbot/experience-hub/commit/1e17cf6daec46857ae601b07d57ca14f47f56023))

## [5.29.3](https://github.com/emma-simbot/experience-hub/compare/v5.29.2...v5.29.3) (2022-12-17)


### Bug Fixes

* add log points when sorting session turns ([d6fef15](https://github.com/emma-simbot/experience-hub/commit/d6fef1511145673e9dd608f3eb4e36d65f48c43c))

## [5.29.2](https://github.com/emma-simbot/experience-hub/compare/v5.29.1...v5.29.2) (2022-12-16)


### Bug Fixes

* add tracing for feature extractor client ([7d82776](https://github.com/emma-simbot/experience-hub/commit/7d82776b8a80dd65629e00fd1ce04d86041a5547))
* add tracing to action prediction client ([bf7b524](https://github.com/emma-simbot/experience-hub/commit/bf7b5240930a22daf3853717de34c956d4bcbdfe))

## [5.29.1](https://github.com/emma-simbot/experience-hub/compare/v5.29.0...v5.29.1) (2022-12-16)


### Bug Fixes

* do not perform healthcheck when handling request from arena ([8b8e66f](https://github.com/emma-simbot/experience-hub/commit/8b8e66f0399b672957c0c1f888a0d3da821b5bf1))
* sort all the session turns when getting from dynamo db ([ce02630](https://github.com/emma-simbot/experience-hub/commit/ce026308562321d14eba79c2648c09061b2ba159))
* stop pinging the S3 bucket during healthcheck ([#230](https://github.com/emma-simbot/experience-hub/issues/230)) ([5395bad](https://github.com/emma-simbot/experience-hub/commit/5395badef2e61f62369b36df2c083e99df360a6e))

## [5.29.0](https://github.com/emma-simbot/experience-hub/compare/v5.28.1...v5.29.0) (2022-12-16)


### Features

* add more tracing to the requests ([#228](https://github.com/emma-simbot/experience-hub/issues/228)) ([190b6de](https://github.com/emma-simbot/experience-hub/commit/190b6de38d148681df3ba63567b74fe3c99aeead))

## [5.28.1](https://github.com/emma-simbot/experience-hub/compare/v5.28.0...v5.28.1) (2022-12-16)


### Bug Fixes

* Correct s3 path for ood models ([#227](https://github.com/emma-simbot/experience-hub/issues/227)) ([991a3e7](https://github.com/emma-simbot/experience-hub/commit/991a3e78b18609014ef61a36ae61591914011e68))
* ensure raw-text matching uses the pipeline guards ([#226](https://github.com/emma-simbot/experience-hub/issues/226)) ([5b9b5c9](https://github.com/emma-simbot/experience-hub/commit/5b9b5c99ebacd273707450409f0c6dfeefc40571)), closes [#222](https://github.com/emma-simbot/experience-hub/issues/222) [#223](https://github.com/emma-simbot/experience-hub/issues/223) [#224](https://github.com/emma-simbot/experience-hub/issues/224) [#214](https://github.com/emma-simbot/experience-hub/issues/214)

## [5.28.0](https://github.com/emma-simbot/experience-hub/compare/v5.27.5...v5.28.0) (2022-12-16)


### Features

* implement search plan ([#208](https://github.com/emma-simbot/experience-hub/issues/208)) ([70ea133](https://github.com/emma-simbot/experience-hub/commit/70ea133a4f7ab8f9595a08cac190823a9068a254))

## [5.27.5](https://github.com/emma-simbot/experience-hub/compare/v5.27.4...v5.27.5) (2022-12-15)


### Bug Fixes

* compound splitter no longer adds to queue if its not needed ([#224](https://github.com/emma-simbot/experience-hub/issues/224)) ([e8b1baa](https://github.com/emma-simbot/experience-hub/commit/e8b1baa37811c27a0baa9eb40396d571c93f8322))

## [5.27.4](https://github.com/emma-simbot/experience-hub/compare/v5.27.3...v5.27.4) (2022-12-15)


### Bug Fixes

* disable compound utterance splitting until further investigation ([00f503e](https://github.com/emma-simbot/experience-hub/commit/00f503e3c6ee2de72f0555bbc1d29910b66909c7))
* guard for checking if user intents exists before checking queue ([0d437e7](https://github.com/emma-simbot/experience-hub/commit/0d437e7c9f9c0c6d7bad81cdb41d06ec597b0c72))

## [5.27.3](https://github.com/emma-simbot/experience-hub/compare/v5.27.2...v5.27.3) (2022-12-15)


### Bug Fixes

* add guards to prevent actions if the utterance is invalid ([#223](https://github.com/emma-simbot/experience-hub/issues/223)) ([71b043b](https://github.com/emma-simbot/experience-hub/commit/71b043b8f1c6284754a63a0b55d64d8b0356c0ce))

## [5.27.2](https://github.com/emma-simbot/experience-hub/compare/v5.27.1...v5.27.2) (2022-12-15)


### Bug Fixes

* **services:** revert to old version of OOD ([#222](https://github.com/emma-simbot/experience-hub/issues/222)) ([3f88f03](https://github.com/emma-simbot/experience-hub/commit/3f88f039ff08762c198557bc0beacb7953dca744))

## [5.27.1](https://github.com/emma-simbot/experience-hub/compare/v5.27.0...v5.27.1) (2022-12-14)


### Bug Fixes

* remove the healthcheck from the startup event ([#221](https://github.com/emma-simbot/experience-hub/issues/221)) ([d975b9d](https://github.com/emma-simbot/experience-hub/commit/d975b9d63994e15a9734a4c13894aa588b07d80d))

## [5.27.0](https://github.com/emma-simbot/experience-hub/compare/v5.26.1...v5.27.0) (2022-12-14)


### Features

* log the clients which fail the healthcheck ([#220](https://github.com/emma-simbot/experience-hub/issues/220)) ([991cec1](https://github.com/emma-simbot/experience-hub/commit/991cec13cc020389193eee2add46398e22bf7205))

## [5.26.1](https://github.com/emma-simbot/experience-hub/compare/v5.26.0...v5.26.1) (2022-12-14)


### Bug Fixes

* path to observability docker compose when running the production ([#219](https://github.com/emma-simbot/experience-hub/issues/219)) ([f4fc37e](https://github.com/emma-simbot/experience-hub/commit/f4fc37e00dd09c1293e7526c9fd3e1a7bd7d74d9))

## [5.26.0](https://github.com/emma-simbot/experience-hub/compare/v5.25.0...v5.26.0) (2022-12-14)


### Features

* improve observability for the API ([#217](https://github.com/emma-simbot/experience-hub/issues/217)) ([4aa11a4](https://github.com/emma-simbot/experience-hub/commit/4aa11a43ef85baba2b589cf5641895101b7c2622))


### Bug Fixes

* need to import future annotations ([#218](https://github.com/emma-simbot/experience-hub/issues/218)) ([0b514e1](https://github.com/emma-simbot/experience-hub/commit/0b514e109acc1278d860e0b6c344d8ba52ba62c1))

## [5.25.0](https://github.com/emma-simbot/experience-hub/compare/v5.24.1...v5.25.0) (2022-12-14)


### Features

* switch to 45 degrees by default when rotating ([#207](https://github.com/emma-simbot/experience-hub/issues/207)) ([9f9aa3f](https://github.com/emma-simbot/experience-hub/commit/9f9aa3f6c7ea2e64b2c4baacf256d4c38bf5127b))

## [5.24.1](https://github.com/emma-simbot/experience-hub/compare/v5.24.0...v5.24.1) (2022-12-13)


### Bug Fixes

* update policy image version to 1.10.2 ([#215](https://github.com/emma-simbot/experience-hub/issues/215)) ([fe8bec4](https://github.com/emma-simbot/experience-hub/commit/fe8bec428a385106abf7341163ec0a29cdc13ffc))

## [5.24.0](https://github.com/emma-simbot/experience-hub/compare/v5.23.2...v5.24.0) (2022-12-13)


### Features

* Add raw text matcher pipeline ([#213](https://github.com/emma-simbot/experience-hub/issues/213)) ([0890932](https://github.com/emma-simbot/experience-hub/commit/08909329b703edec168cef41895ea65d046dbe7c))

## [5.23.2](https://github.com/emma-simbot/experience-hub/compare/v5.23.1...v5.23.2) (2022-12-13)


### Bug Fixes

* **docker:** `LOG_LEVEL` for compound splitter service needs to be lowercase ([f3d947c](https://github.com/emma-simbot/experience-hub/commit/f3d947c5d00385e8ff3fd8f515e7d4f2510b81fd))

## [5.23.1](https://github.com/emma-simbot/experience-hub/compare/v5.23.0...v5.23.1) (2022-12-10)


### Bug Fixes

* **deployment:** add compound splitter to the docker compose ([#211](https://github.com/emma-simbot/experience-hub/issues/211)) ([705a875](https://github.com/emma-simbot/experience-hub/commit/705a875b012be310c93dddb0dfae6801761dac18))

## [5.23.0](https://github.com/emma-simbot/experience-hub/compare/v5.22.0...v5.23.0) (2022-12-08)


### Features

* **parser:** Add compound instruction splitter ([#130](https://github.com/emma-simbot/experience-hub/issues/130)) ([98797da](https://github.com/emma-simbot/experience-hub/commit/98797da113686a886d489acb530c2cf469a218ae))

## [5.22.0](https://github.com/emma-simbot/experience-hub/compare/v5.21.1...v5.22.0) (2022-12-08)


### Features

* Implement goto after highlight in search ([#200](https://github.com/emma-simbot/experience-hub/issues/200)) ([4304aab](https://github.com/emma-simbot/experience-hub/commit/4304aab3f496902d524c4cb21437226daa496aad))

## [5.21.1](https://github.com/emma-simbot/experience-hub/compare/v5.21.0...v5.21.1) (2022-12-08)


### Bug Fixes

* arena error statuses also need to be intents ([#206](https://github.com/emma-simbot/experience-hub/issues/206)) ([7a15eea](https://github.com/emma-simbot/experience-hub/commit/7a15eea421d5bd7923eb6f6565c6c85190bae4dc))

## [5.21.0](https://github.com/emma-simbot/experience-hub/compare/v5.20.0...v5.21.0) (2022-12-08)


### Features

* include/support alias types for the Goto action ([#203](https://github.com/emma-simbot/experience-hub/issues/203)) ([ce8802c](https://github.com/emma-simbot/experience-hub/commit/ce8802c4ebef6d1f04222e46fb783081384090af))

## [5.20.0](https://github.com/emma-simbot/experience-hub/compare/v5.19.0...v5.20.0) (2022-12-08)


### Features

* added support for new errors ([#202](https://github.com/emma-simbot/experience-hub/issues/202)) ([717ab08](https://github.com/emma-simbot/experience-hub/commit/717ab0816455308f8bba7d4dc3c19f27de2f9b9c))

## [5.19.0](https://github.com/emma-simbot/experience-hub/compare/v5.18.3...v5.19.0) (2022-12-07)


### Features

* update nlu model and enable search ([#199](https://github.com/emma-simbot/experience-hub/issues/199)) ([63ddd3e](https://github.com/emma-simbot/experience-hub/commit/63ddd3e4bd385c2db75a4b81eb5b5eeb8d5d7896))

## [5.18.3](https://github.com/emma-simbot/experience-hub/compare/v5.18.2...v5.18.3) (2022-12-06)


### Bug Fixes

* remove placeholder button detector ([#198](https://github.com/emma-simbot/experience-hub/issues/198)) ([97c802c](https://github.com/emma-simbot/experience-hub/commit/97c802ca87bd8d99ae9b24e1c8bf3f3b748cb2be))
* remove the placeholder client from the `__init__.py` ([0f5bbc2](https://github.com/emma-simbot/experience-hub/commit/0f5bbc2a3d58a6847bb23867afb546d38b76daa5))

## [5.18.2](https://github.com/emma-simbot/experience-hub/compare/v5.18.1...v5.18.2) (2022-12-05)


### Bug Fixes

* set default number of workers to 4 ([ef96404](https://github.com/emma-simbot/experience-hub/commit/ef96404586341f1c5487194fdf7baa2507bd7d43))

## [5.18.1](https://github.com/emma-simbot/experience-hub/compare/v5.18.0...v5.18.1) (2022-12-05)


### Bug Fixes

* do not re-serialise the response model to `SimBotResponse` on returning endpoint ([#196](https://github.com/emma-simbot/experience-hub/issues/196)) ([8f08fe0](https://github.com/emma-simbot/experience-hub/commit/8f08fe04f42542038ecbd3f89d1abe4258e8b1d3))

## [5.18.0](https://github.com/emma-simbot/experience-hub/compare/v5.17.0...v5.18.0) (2022-12-05)


### Features

* **cli:** add option to force download all models if desired ([b1b9a6d](https://github.com/emma-simbot/experience-hub/commit/b1b9a6dbb1697759ee9df91665eaa3dcf12e829e))


### Bug Fixes

* **registry:** feature extractor version did not exist ([193e86d](https://github.com/emma-simbot/experience-hub/commit/193e86d9c4f5483cf798d5a45f5c0289f90be2fb))
* **registry:** remove file hash from the downloaded model file name ([1503d10](https://github.com/emma-simbot/experience-hub/commit/1503d105adefeb69aeffe21ca941b84c53b30a46))

## [5.17.0](https://github.com/emma-simbot/experience-hub/compare/v5.16.0...v5.17.0) (2022-12-02)


### Features

* default the number of workers in production to 8 ([e2c9bf4](https://github.com/emma-simbot/experience-hub/commit/e2c9bf4d89b8db9553ce0ab155a5fa3c38586d74))


### Bug Fixes

* improve how dialog intents are retrieved from previous actions ([#190](https://github.com/emma-simbot/experience-hub/issues/190)) ([e00e15f](https://github.com/emma-simbot/experience-hub/commit/e00e15fac9f5a45bb384a01a2bdd11a67eb8e91c))

## [5.16.0](https://github.com/emma-simbot/experience-hub/compare/v5.15.0...v5.16.0) (2022-12-01)


### Features

* run server with gunicorn and multiple workers ([#191](https://github.com/emma-simbot/experience-hub/issues/191)) ([1e5cf8b](https://github.com/emma-simbot/experience-hub/commit/1e5cf8bbe0e471f04c3a37bc8045231af575dc98))

## [5.15.0](https://github.com/emma-simbot/experience-hub/compare/v5.14.0...v5.15.0) (2022-12-01)


### Features

* include handling for search predictions in language generation pipeline ([4a9252e](https://github.com/emma-simbot/experience-hub/commit/4a9252eb041aa2021b014aeccb9d1b90da55aef3))


### Bug Fixes

* action type for the look around action in find object pipeline ([397aa38](https://github.com/emma-simbot/experience-hub/commit/397aa3822db69f7548457bab6731df78acb14624))
* add a lot more logs to the language generation pipeline ([5bb470b](https://github.com/emma-simbot/experience-hub/commit/5bb470b89c0394ab93bf8e70498dd93bd6f328e8))
* add entity name property to goto viewpoint payload ([8526e5b](https://github.com/emma-simbot/experience-hub/commit/8526e5b02ae30983ef325f9e9640c2bead7ef58c))
* improve detection of whether we should continue the search routine ([6b14c0d](https://github.com/emma-simbot/experience-hub/commit/6b14c0d0f3f11ec1c0cc3dd5852923aaebabb402))
* **registry/download:** append file hash to downloaded model file name ([dbaf6e3](https://github.com/emma-simbot/experience-hub/commit/dbaf6e39fd436500447f887aa64048f89a4c633a))
* remove entity type from simbot dialog action payload since its not a valid field ([e87bb07](https://github.com/emma-simbot/experience-hub/commit/e87bb0793da5e1e002c345ada3d7f7cd0e87d49a))
* separate responding to confirmation request from the clarify answer path ([4aa6c44](https://github.com/emma-simbot/experience-hub/commit/4aa6c4441620f36dd09bc09176846bba5707c9e9))

## [5.14.0](https://github.com/emma-simbot/experience-hub/compare/v5.13.0...v5.14.0) (2022-12-01)


### Features

* use simbot action model with custom classes ([#189](https://github.com/emma-simbot/experience-hub/issues/189)) ([57569b4](https://github.com/emma-simbot/experience-hub/commit/57569b4569c2742029f128e0ead05d53846e890f))

## [5.13.0](https://github.com/emma-simbot/experience-hub/compare/v5.12.1...v5.13.0) (2022-12-01)


### Features

* add utterances for the search intents ([#187](https://github.com/emma-simbot/experience-hub/issues/187)) ([1562135](https://github.com/emma-simbot/experience-hub/commit/1562135310259d80795328d3eb5ccb27b1bc1a62))

## [5.12.1](https://github.com/emma-simbot/experience-hub/compare/v5.12.0...v5.12.1) (2022-11-30)


### Bug Fixes

* condition when we should start a new search plan ([#184](https://github.com/emma-simbot/experience-hub/issues/184)) ([bde9b2d](https://github.com/emma-simbot/experience-hub/commit/bde9b2df2aec477e077ebd2f177ebf675baaf131))

## [5.12.0](https://github.com/emma-simbot/experience-hub/compare/v5.11.0...v5.12.0) (2022-11-30)


### Features

* agent should continue with search if its in progress ([#183](https://github.com/emma-simbot/experience-hub/issues/183)) ([4568212](https://github.com/emma-simbot/experience-hub/commit/456821287aa81afd1e771e7bb946cef9453dff9b))


### Bug Fixes

* reset the queue when an object has been found ([#185](https://github.com/emma-simbot/experience-hub/issues/185)) ([46e6b71](https://github.com/emma-simbot/experience-hub/commit/46e6b713ce3807f1c8cabeeb7965b2b73824772e))

## [5.11.0](https://github.com/emma-simbot/experience-hub/compare/v5.10.0...v5.11.0) (2022-11-30)


### Features

* **clients:** implement request to finding object in scene ([#181](https://github.com/emma-simbot/experience-hub/issues/181)) ([685901a](https://github.com/emma-simbot/experience-hub/commit/685901ae1c9c1b710552c29e72c8cef7851c9ffb))

## [5.10.0](https://github.com/emma-simbot/experience-hub/compare/v5.9.0...v5.10.0) (2022-11-30)


### Features

* support continuing search after confirmation questions and converting highlight to goto action ([#180](https://github.com/emma-simbot/experience-hub/issues/180)) ([2ca0b8f](https://github.com/emma-simbot/experience-hub/commit/2ca0b8f24e12a583443f685efda81f8b46c6c082))

## [5.9.0](https://github.com/emma-simbot/experience-hub/compare/v5.8.0...v5.9.0) (2022-11-30)


### Features

* easily get progress of find object routine from the session state ([#179](https://github.com/emma-simbot/experience-hub/issues/179)) ([e4b9c24](https://github.com/emma-simbot/experience-hub/commit/e4b9c24d48e257974bf18fd0fb2b4e43dd878ebc))
* **pipeline:** create pipeline to find objects in the arena ([#176](https://github.com/emma-simbot/experience-hub/issues/176)) ([9e60eb4](https://github.com/emma-simbot/experience-hub/commit/9e60eb4fc3520f0aa8bd7ae7f24f1ec8d360144a))

## [5.8.0](https://github.com/emma-simbot/experience-hub/compare/v5.7.0...v5.8.0) (2022-11-30)


### Features

* include the confirmation response classifier ([#161](https://github.com/emma-simbot/experience-hub/issues/161)) ([6e97d7e](https://github.com/emma-simbot/experience-hub/commit/6e97d7e3448cc9f33b730ef265588b0f9f62a3e3))

## [5.7.0](https://github.com/emma-simbot/experience-hub/compare/v5.6.1...v5.7.0) (2022-11-30)


### Features

* **parser:** implement parser to handle the `<act><previous>` intent type ([#174](https://github.com/emma-simbot/experience-hub/issues/174)) ([825b791](https://github.com/emma-simbot/experience-hub/commit/825b791a43a80ce5d6abae3fe61e143c9ba20b20))

## [5.6.1](https://github.com/emma-simbot/experience-hub/compare/v5.6.0...v5.6.1) (2022-11-29)


### Bug Fixes

* only use the object class within the payload when the action type is `Examine` ([#171](https://github.com/emma-simbot/experience-hub/issues/171)) ([21fb9a8](https://github.com/emma-simbot/experience-hub/commit/21fb9a8f594df011ab0147b777d9316b72cffb2f))

## [5.6.0](https://github.com/emma-simbot/experience-hub/compare/v5.5.0...v5.6.0) (2022-11-29)


### Features

* support getting the closest viewpoint to the agent for a given turn ([#166](https://github.com/emma-simbot/experience-hub/issues/166)) ([d394489](https://github.com/emma-simbot/experience-hub/commit/d394489801a9eab4a4693fd17a8b478c4e4fdf14))

## [5.5.0](https://github.com/emma-simbot/experience-hub/compare/v5.4.0...v5.5.0) (2022-11-29)


### Features

* **intents:** add intents for feedback during search loop ([#170](https://github.com/emma-simbot/experience-hub/issues/170)) ([9ab7250](https://github.com/emma-simbot/experience-hub/commit/9ab72500a7d7fccd01829dbadb7c3e223685e692))

## [5.4.0](https://github.com/emma-simbot/experience-hub/compare/v5.3.0...v5.4.0) (2022-11-29)


### Features

* **parser:** create a skeleton for the `SimBotVisualGroundingOutputParser` ([#169](https://github.com/emma-simbot/experience-hub/issues/169)) ([1a48bc5](https://github.com/emma-simbot/experience-hub/commit/1a48bc594fcc6b722ec40b051212760ddfe9340c))

## [5.3.0](https://github.com/emma-simbot/experience-hub/compare/v5.2.1...v5.3.0) (2022-11-29)


### Features

* add a new queue to track things in the state ([#165](https://github.com/emma-simbot/experience-hub/issues/165)) ([950b3f7](https://github.com/emma-simbot/experience-hub/commit/950b3f7a8141dec0dc35fa7ee7cc058dde547545))

## [5.2.1](https://github.com/emma-simbot/experience-hub/compare/v5.2.0...v5.2.1) (2022-11-29)


### Bug Fixes

* importerror for loguru's contextualizer ([4dde50d](https://github.com/emma-simbot/experience-hub/commit/4dde50d42d0b37c90dd231eeb48cd441bc5917a3))
* linting error ([7c4fc55](https://github.com/emma-simbot/experience-hub/commit/7c4fc55bd28909355883b86764855816e7f3bcdf))

## [5.2.0](https://github.com/emma-simbot/experience-hub/compare/v5.1.1...v5.2.0) (2022-11-25)


### Features

* contextualise CloudWatch logs with identifiers for OpenSearch ([#164](https://github.com/emma-simbot/experience-hub/issues/164)) ([7a16dfc](https://github.com/emma-simbot/experience-hub/commit/7a16dfcde06321480beb7f38f4c13e746b146a75))

## [5.1.1](https://github.com/emma-simbot/experience-hub/compare/v5.1.0...v5.1.1) (2022-11-25)


### Bug Fixes

* manually change parsed intent type if it predicts the old act intent ([#163](https://github.com/emma-simbot/experience-hub/issues/163)) ([dfa7d4b](https://github.com/emma-simbot/experience-hub/commit/dfa7d4b1830d26ac323f91b15f794f3ca55981e7))

## [5.1.0](https://github.com/emma-simbot/experience-hub/compare/v5.0.2...v5.1.0) (2022-11-25)


### Features

* improve the logging format for OpenSearch ([#162](https://github.com/emma-simbot/experience-hub/issues/162)) ([945a222](https://github.com/emma-simbot/experience-hub/commit/945a222dad608b28ab74f088b3d347f066e3ed10))

## [5.0.2](https://github.com/emma-simbot/experience-hub/compare/v5.0.1...v5.0.2) (2022-11-25)


### Bug Fixes

* put disable search action flag in the agent intent selection pipeline ([08fb882](https://github.com/emma-simbot/experience-hub/commit/08fb882c7c5ca64d34d5b24fa58d31610727c31d))
* remove disable search action flag within agent action generation pipeline ([ff8b803](https://github.com/emma-simbot/experience-hub/commit/ff8b8030200b1f7b4d1b5de36f57d8d372faacd1))

## [5.0.1](https://github.com/emma-simbot/experience-hub/compare/v5.0.0...v5.0.1) (2022-11-24)


### Bug Fixes

* added support for action execution error ([#158](https://github.com/emma-simbot/experience-hub/issues/158)) ([754e240](https://github.com/emma-simbot/experience-hub/commit/754e240eb9aba1fd60d5927c467bc4a567ed167d))

## [5.0.0](https://github.com/emma-simbot/experience-hub/compare/v4.0.1...v5.0.0) (2022-11-24)


### ⚠ BREAKING CHANGES

* Handle value change for `SimBotIntentType.act` (#151)

### Features

* Handle value change for `SimBotIntentType.act` ([#151](https://github.com/emma-simbot/experience-hub/issues/151)) ([b0448fe](https://github.com/emma-simbot/experience-hub/commit/b0448fe772fd3e35fefe997c12b400405a2a03ce)), closes [#150](https://github.com/emma-simbot/experience-hub/issues/150)

## [4.0.1](https://github.com/emma-simbot/experience-hub/compare/v4.0.0...v4.0.1) (2022-11-21)


### Bug Fixes

* added extra check for sticky note ([#152](https://github.com/emma-simbot/experience-hub/issues/152)) ([69d5fcb](https://github.com/emma-simbot/experience-hub/commit/69d5fcb7bc6a28406a8876563e0ca5ca969061f9))
* upgraded perception with correct classmap ([#157](https://github.com/emma-simbot/experience-hub/issues/157)) ([2992168](https://github.com/emma-simbot/experience-hub/commit/2992168ed328e1856bbbfecb211872e31557ff20))

## [4.0.0](https://github.com/emma-simbot/experience-hub/compare/v3.5.3...v4.0.0) (2022-11-18)


### ⚠ BREAKING CHANGES

* track state across turns and be able to act on the queue (#148)

### Features

* track state across turns and be able to act on the queue ([#148](https://github.com/emma-simbot/experience-hub/issues/148)) ([dddd11f](https://github.com/emma-simbot/experience-hub/commit/dddd11f78a7b61049f374841d6c48339fec6ede7))

## [3.5.3](https://github.com/emma-simbot/experience-hub/compare/v3.5.2...v3.5.3) (2022-11-18)


### Bug Fixes

* **cli:** send logs to cloudwatch every minute ([29316ae](https://github.com/emma-simbot/experience-hub/commit/29316ae66c5bbc92f750f94dd432f4ceb23abbe9))

## [3.5.2](https://github.com/emma-simbot/experience-hub/compare/v3.5.1...v3.5.2) (2022-11-15)


### Bug Fixes

* add `arena_unavailable` error to the list of environment errors ([70adfc3](https://github.com/emma-simbot/experience-hub/commit/70adfc38588bbf626773230f197f324efd308d16))

## [3.5.1](https://github.com/emma-simbot/experience-hub/compare/v3.5.0...v3.5.1) (2022-11-15)


### Bug Fixes

* make sure new action status types have intents for them ([9bb75ba](https://github.com/emma-simbot/experience-hub/commit/9bb75ba27e746f0178af7d7f2f528dd3b56da02f))

## [3.5.0](https://github.com/emma-simbot/experience-hub/compare/v3.4.1...v3.5.0) (2022-11-15)


### Features

* use synonyms for action and room names ([#145](https://github.com/emma-simbot/experience-hub/issues/145)) ([3ed883c](https://github.com/emma-simbot/experience-hub/commit/3ed883ce9c6667aad7cd8b9c00d8b7c031fa77e8)), closes [#144](https://github.com/emma-simbot/experience-hub/issues/144)

## [3.4.1](https://github.com/emma-simbot/experience-hub/compare/v3.4.0...v3.4.1) (2022-11-15)


### Bug Fixes

* do not include intent type in dialog payload ([2614119](https://github.com/emma-simbot/experience-hub/commit/2614119b83054bf0725cbef71ba35b01c0b75bb5))

## [3.4.0](https://github.com/emma-simbot/experience-hub/compare/v3.3.0...v3.4.0) (2022-11-15)


### Features

* support updated arena error types ([#143](https://github.com/emma-simbot/experience-hub/issues/143)) ([7b43747](https://github.com/emma-simbot/experience-hub/commit/7b437477131cd1533df4c7a65c92c93c5cb557e2))

## [3.3.0](https://github.com/emma-simbot/experience-hub/compare/v3.2.0...v3.3.0) (2022-11-15)


### Features

* support the new lightweight dialog action ([#142](https://github.com/emma-simbot/experience-hub/issues/142)) ([75842ed](https://github.com/emma-simbot/experience-hub/commit/75842eda5b6f63821622bff5765b3c69e50e5aff))

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
