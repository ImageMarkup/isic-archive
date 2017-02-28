###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

add_python_style_test(
  python_static_analysis_isic_archive
  "${CMAKE_CURRENT_LIST_DIR}/server")
add_python_style_test(
  python_static_analysis_isic_archive_tests
  "${CMAKE_CURRENT_LIST_DIR}/plugin_tests")
add_python_style_test(
  python_static_analysis_isic_archive_scripts
  "${CMAKE_CURRENT_LIST_DIR}/scripts")

add_python_test(
  user
  PLUGIN isic_archive)
add_python_test(
  upload
  PLUGIN isic_archive
  EXTERNAL_DATA
    "plugins/isic_archive/test_1_small_1.jpg"
    "plugins/isic_archive/test_1_small_2.jpg"
    "plugins/isic_archive/test_1_small_3.jpg"
    "plugins/isic_archive/test_1_large_1.jpg"
    "plugins/isic_archive/test_1_large_2.jpg"
    "plugins/isic_archive/test_1_metadata.csv")
add_python_test(
  segmentation_helper
  PLUGIN isic_archive)

add_eslint_test(
  isic_archive_external
  "${CMAKE_CURRENT_LIST_DIR}/web_external"
  ESLINT_CONFIG_FILE "${CMAKE_CURRENT_LIST_DIR}/web_external/.eslintrc.js"
  ESLINT_IGNORE_FILE "${CMAKE_CURRENT_LIST_DIR}/web_external/.eslintignore")
add_eslint_test(
    isic_archive
    "${CMAKE_CURRENT_LIST_DIR}/web_client/js")
add_eslint_test(
    isic_archive_grunt
    "${CMAKE_CURRENT_LIST_DIR}/Gruntfile.js")
