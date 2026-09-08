/**
 * Comprehensive Broken-Link & Asset Crawler
 * Inspects all canonical HTML files in frontend/ and verifies that every:
 * - <a> navigation href
 * - <script> source
 * - <link> stylesheet
 * - <img> source
 * - <video poster> source
 * points to a valid file on disk and returns HTTP 200 when fetched from the local server.
 */
const fs = require('fs');
const path = require('path');
const http = require('http');

const FRONTEND_DIR = path.resolve(__dirname, '../frontend');
const BASE_URL = 'http://localhost';

// Discover all HTML files
function getHtmlFiles(dir) {
  let results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results = results.concat(getHtmlFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      results.push(fullPath);
    }
  }
  return results;
}

// Simple regex parser for attributes
function extractAttributes(html, tag, attr) {
  const regex = new RegExp(`<${tag}[^>]*\\s+${attr}=["']([^"']+)["']`, 'gi');
  const matches = [];
  let match;
  while ((match = regex.exec(html)) !== null) {
    matches.push(match[1]);
  }
  return matches;
}

function checkHttpStatus(urlPath) {
  return new Promise((resolve) => {
    const target = `${BASE_URL}${urlPath.startsWith('/') ? '' : '/'}${urlPath}`;
    http.get(target, (res) => {
      resolve({ status: res.statusCode, url: target });
    }).on('error', (err) => {
      resolve({ status: 0, error: err.message, url: target });
    });
  });
}

async function runCrawler() {
  console.log('====================================================');
  console.log('PHASE 3B: BROKEN LINK & ASSET CRAWLER');
  console.log('====================================================\n');

  const htmlFiles = getHtmlFiles(FRONTEND_DIR);
  console.log(`Found ${htmlFiles.length} canonical HTML documents to audit.\n`);

  const defects = [];
  let totalChecked = 0;

  for (const htmlFile of htmlFiles) {
    const relFile = path.relative(FRONTEND_DIR, htmlFile);
    const content = fs.readFileSync(htmlFile, 'utf8');
    const fileDir = path.dirname(htmlFile);

    const links = [
      ...extractAttributes(content, 'a', 'href').map(u => ({ type: 'link', url: u })),
      ...extractAttributes(content, 'script', 'src').map(u => ({ type: 'script', url: u })),
      ...extractAttributes(content, 'link', 'href').map(u => ({ type: 'stylesheet/link', url: u })),
      ...extractAttributes(content, 'img', 'src').map(u => ({ type: 'image', url: u })),
      ...extractAttributes(content, 'video', 'poster').map(u => ({ type: 'video-poster', url: u })),
      ...extractAttributes(content, 'source', 'src').map(u => ({ type: 'source', url: u }))
    ];

    for (const item of links) {
      const rawUrl = item.url.trim();

      // Skip external, protocol-relative, anchors, mailto, javascript, data URIs
      if (
        !rawUrl ||
        rawUrl.startsWith('http://') ||
        rawUrl.startsWith('https://') ||
        rawUrl.startsWith('//') ||
        rawUrl.startsWith('#') ||
        rawUrl.startsWith('mailto:') ||
        rawUrl.startsWith('tel:') ||
        rawUrl.startsWith('javascript:') ||
        rawUrl.startsWith('data:')
      ) {
        continue;
      }

      totalChecked++;

      // Strip query params and hash for filesystem check
      const cleanUrl = rawUrl.split('?')[0].split('#')[0];

      // Resolve local filesystem path
      let resolvedDiskPath;
      let serverUrlPath;

      if (cleanUrl.startsWith('/')) {
        resolvedDiskPath = path.join(FRONTEND_DIR, cleanUrl);
        serverUrlPath = cleanUrl;
      } else {
        resolvedDiskPath = path.resolve(fileDir, cleanUrl);
        const relToFrontend = path.relative(FRONTEND_DIR, resolvedDiskPath);
        serverUrlPath = '/' + relToFrontend.replace(/\\/g, '/');
      }

      // 1. Check local file existence on disk
      const existsOnDisk = fs.existsSync(resolvedDiskPath);
      if (!existsOnDisk) {
        defects.push({
          sourceDocument: relFile,
          resourceType: item.type,
          referencedUrl: rawUrl,
          resolvedDiskPath,
          issue: 'FILE_NOT_FOUND_ON_DISK',
          status: 404
        });
        continue;
      }

      // 2. Check HTTP status from local server
      const httpResult = await checkHttpStatus(serverUrlPath);
      if (httpResult.status !== 200) {
        defects.push({
          sourceDocument: relFile,
          resourceType: item.type,
          referencedUrl: rawUrl,
          serverUrl: httpResult.url,
          issue: `HTTP_STATUS_${httpResult.status}`,
          status: httpResult.status
        });
      }
    }
  }

  console.log(`Audited ${totalChecked} internal links, scripts, stylesheets, and media references.`);
  console.log(`Total defects found: ${defects.length}\n`);

  if (defects.length > 0) {
    console.error('DEFECT LIST:');
    console.table(defects);
    process.exit(1);
  } else {
    console.log('SUCCESS: All internal links and assets resolved with HTTP 200.');
    process.exit(0);
  }
}

runCrawler();
