#!/bin/sh
# Publishes the newest version of releases.toml when a merge into main brings a new one
# (ADR 0009, ADR 0010).
# Run by the pipeline's `release` job, after every stage passed:
#
#   .github/scripts/release.sh
#
# 1. Puts the version's tag (e.g. `1.4.2`) on the three images this run just
#    built and tested (`sha-<commit>`). Nothing is rebuilt, so production runs
#    exactly what passed. The tag goes on the first image of each version and
#    never moves: a merge that adds no version publishes nothing.
# 2. Creates the GitHub release vX.Y.Z, its title and notes written from releases.toml
#    ("1.4.2 – <title>", "- **Fix · Orders:** <text>", Dependabot's marked "(Dependabot, #N)").
#
# The server then puts the newest version in production by itself
# (docs/DEPLOY.md#releasing-a-version).
#
# Needs GITHUB_SHA, `gh` with GH_TOKEN (contents: write) and a `docker login
# ghcr.io` that can push the packages. REGISTRY is only changed by tests.
set -eu

registry=${REGISTRY:-ghcr.io/senatoreteam}
images="api web worker"
commit=${GITHUB_SHA:?}

fail() {
	echo "::error::$*" >&2
	exit 1
}

python3 -I .github/scripts/releases.py > /dev/null || fail "releases.toml or README.md is not right (see the lint)."
version=$(python3 -I .github/scripts/releases.py --version)
tag=v$version

exists() {
	docker buildx imagetools inspect "$1" > /dev/null 2>&1
}
revision() {
	docker buildx imagetools inspect "$1" --format '{{index .Image.Config.Labels "org.opencontainers.image.revision"}}'
}

published=0
for image in $images; do
	if exists "$registry/slicepizza-$image:$version"; then
		published=$((published + 1))
	fi
done

if [ "$published" -eq 3 ]; then
	# The version's images came from the first commit that had this version.
	target=$(revision "$registry/slicepizza-api:$version")
	echo "Version $version is already published (images of $target)."
elif [ "$published" -eq 0 ]; then
	target=$commit
	short=$(printf '%.7s' "$commit")
	for image in $images; do
		source="$registry/slicepizza-$image:sha-$short"
		exists "$source" || fail "$source does not exist: the images stage should have published it."
		# sha-<short> could in theory match two commits: the image says which one it is.
		built_from=$(revision "$source")
		[ "$built_from" = "$commit" ] || fail "$source was built from '$built_from', not from $commit."
	done
	for image in $images; do
		docker buildx imagetools create --tag "$registry/slicepizza-$image:$version" "$registry/slicepizza-$image:sha-$short"
		echo "$registry/slicepizza-$image:$version -> sha-$short"
	done
else
	fail "Only $published of the 3 images have the tag $version. Fix it by hand: a version is all three or none."
fi

# The release, unless it exists (a re-run after the images were tagged).
if gh release view "$tag" > /dev/null 2>&1; then
	echo "The release $tag already exists."
else
	notes=$(mktemp)
	python3 -I .github/scripts/releases.py --notes "$version" > "$notes"
	gh release create "$tag" --target "$target" --title "$(python3 -I .github/scripts/releases.py --title "$version")" \
		--notes-file "$notes" --latest
	echo "Created the release $tag."
fi

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
	{
		echo "### Version $version"
		echo
		echo "Images of commit \`$target\`. The server puts the newest version in production within a few minutes (docs/DEPLOY.md)."
		echo
		for image in $images; do
			echo "- \`$registry/slicepizza-$image:$version\`"
		done
	} >> "$GITHUB_STEP_SUMMARY"
fi
