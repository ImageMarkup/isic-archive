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

# Extended add_eslint_test to lint .vue files in addition to .js files
function(add_eslint_test_ext name input)
  if (NOT JAVASCRIPT_STYLE_TESTS)
    return()
  endif()

  add_test(
    NAME "eslint_${name}"
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    COMMAND npx eslint --ext .js,.vue "${input}"
  )
  set_property(TEST "eslint_${name}" PROPERTY LABELS girder_browser)
endfunction()

add_standard_plugin_tests(NO_SERVER)

# Fetch external data
set(_data_files "")
foreach(_data_file
  "plugins/isic_archive/test_1_small_1.jpg"
  "plugins/isic_archive/test_1_small_2.jpg"
  "plugins/isic_archive/test_1_small_3.jpg"
  "plugins/isic_archive/test_1_large_1.jpg"
  "plugins/isic_archive/test_1_large_2.jpg"
  "plugins/isic_archive/test_1_metadata.csv"
)
  list(APPEND _data_files "DATA{${GIRDER_EXTERNAL_DATA_BUILD_PATH}/${_data_file}}")
endforeach()
girder_ExternalData_expand_arguments("${name}_data" _tmp ${_data_files})
girder_ExternalData_add_target("${name}_data")

# External client static analysis
add_eslint_test_ext(
  isic_archive_external
  "${CMAKE_CURRENT_LIST_DIR}/isic-archive-gui/src")
add_test(
  NAME puglint_isic_archive_external
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
  COMMAND npx pug-lint -c "${CMAKE_CURRENT_LIST_DIR}/isic-archive-gui/.pug-lintrc" "${CMAKE_CURRENT_LIST_DIR}/isic-archive-gui/src")
set_property(TEST puglint_isic_archive_external PROPERTY LABELS girder_browser)
add_stylint_test(
  isic_archive_external
  "${CMAKE_CURRENT_LIST_DIR}/isic-archive-gui/src")
