#!/bin/bash
${GRAALVM_JAVA_HOME}/bin/java -agentlib:native-image-agent=config-merge-dir="${TRACE_METADATA_DIRECTORY}" "$@"
