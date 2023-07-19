#!/bin/bash
${GRAALVM_JAVA_HOME}/bin/java -agentlib:native-image-agent=config-output-dir="${TRACE_METADATA_DIRECTORY}" "$@"
