#!/usr/bin/env node

const fs = require('fs');
const { execSync } = require('child_process');

const versionType = process.argv[2] || 'patch';

if (!['patch', 'minor', 'major'].includes(versionType)) {
  console.error('Usage: node bump-version.js [patch|minor|major]');
  process.exit(1);
}

try {
  // Bump package.json version
  execSync(`npm version ${versionType} --no-git-tag-version`, { stdio: 'inherit' });
  
  // Get new version
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const newVersion = packageJson.version;
  
  // Update agent version
  fs.writeFileSync('agents/version.txt', newVersion);
  
  // Commit changes
  execSync('git add package.json agents/version.txt', { stdio: 'inherit' });
  execSync(`git commit -m "Bump version to ${newVersion}"`, { stdio: 'inherit' });
  
  console.log(`✅ Version bumped to ${newVersion}`);
  console.log('🚀 Push to trigger automatic release: git push origin main');
  
} catch (error) {
  console.error('❌ Version bump failed:', error.message);
  process.exit(1);
}