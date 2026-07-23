import argparse
import os
import subprocess
import shutil

def create_package_json(name):
    content = f"""{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "Looker Custom Visualization: {name}",
  "main": "dist/viz_bundle.js",
  "scripts": {{
    "build": "webpack --mode production",
    "dev": "webpack serve --config webpack.config.js"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "prop-types": "^15.8.1",
    "styled-components": "^6.0.0",
    "ag-grid-community": "^31.0.0",
    "ag-grid-react": "^31.0.0"
  }},
  "devDependencies": {{
    "@babel/core": "^7.23.0",
    "@babel/preset-env": "^7.23.0",
    "@babel/preset-react": "^7.23.0",
    "babel-loader": "^9.1.0",
    "css-loader": "^6.8.0",
    "style-loader": "^3.3.0",
    "webpack": "^5.88.0",
    "webpack-cli": "^5.1.0",
    "webpack-dev-server": "^4.15.0"
  }}
}}"""
    with open("package.json", "w") as f:
        f.write(content)
    print("Created package.json")

def create_webpack_config(name):
    content = """const path = require('path');
const fs = require('fs');

// Check for local certificates
const certKeyPath = path.join(__dirname, 'localhost-key.pem');
const certPath = path.join(__dirname, 'localhost.pem');
const useHttps = fs.existsSync(certKeyPath) && fs.existsSync(certPath);

module.exports = {
  mode: 'production',
  entry: './src/index.js',
  output: {
    filename: 'viz_bundle.js',
    path: path.resolve(__dirname, 'dist'),
    library: 'custom_viz',
    libraryTarget: 'umd',
  },
  resolve: {
    extensions: ['.js', '.jsx'],
  },
  module: {
    rules: [
      {
        test: /\\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
          },
        },
      },
      {
        test: /\\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    compress: true,
    port: 8080,
    server: useHttps ? {
      type: 'https',
      options: {
        key: fs.readFileSync(certKeyPath),
        cert: fs.readFileSync(certPath),
      },
    } : 'http',
    allowedHosts: 'all',
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization",
      "Access-Control-Allow-Private-Network": "true"
    }
  }
};"""
    with open("webpack.config.js", "w") as f:
        f.write(content)
    print("Created webpack.config.js")

def setup_harness():
    os.makedirs("harness", exist_ok=True)
    
    # Path to assets in the skill directory
    assets_dir = "/usr/local/google/home/adamminton/.gemini/jetski/global_skills/looker-custom-viz/assets/harness"
    
    # Copy assets
    if os.path.exists(assets_dir):
        shutil.copy(os.path.join(assets_dir, "builder.html"), "harness/builder.html")
        shutil.copy(os.path.join(assets_dir, "mocks.js"), "harness/mocks.js")
    else:
        print(f"Warning: Asset directory {assets_dir} not found. Creating empty harness files.")
        open("harness/builder.html", "w").close()
        open("harness/mocks.js", "w").close()

    # Create empty data_scenarios.js if not exists
    if not os.path.exists("harness/data_scenarios.js"):
        with open("harness/data_scenarios.js", "w") as f:
            f.write("window.scenarios = {};")
    
    print("Setup harness/")

def create_src_scaffold(name):
    os.makedirs("src", exist_ok=True)
    
    # Simple index.js entry point
    index_content = """import React from 'react';
import { createRoot } from 'react-dom/client';

looker.plugins.visualizations.add({
  id: 'custom_viz',
  label: 'Custom Visualization',
  options: {
    // Add options here
  },
  create: function(element, config) {
    this._root = createRoot(element);
  },
  updateAsync: function(data, element, config, queryResponse, details, done) {
    this._root.render(
      <div style={{ padding: '20px' }}>
        <h1>It Works!</h1>
        <p>This is your new custom visualization.</p>
        <pre>{JSON.stringify(data[0], null, 2)}</pre>
      </div>
    );
    done();
  }
});"""
    
    with open("src/index.js", "w") as f:
        f.write(index_content)
    print("Created src/index.js")

def main():
    parser = argparse.ArgumentParser(description="Initialize Standalone Looker Viz")
    parser.add_argument("--name", default="my-looker-viz", help="Project name")
    args = parser.parse_args()

    print(f"Initializing {args.name}...")
    
    create_package_json(args.name)
    create_webpack_config(args.name)
    setup_harness()
    create_src_scaffold(args.name)
    
    # Gitignore
    with open(".gitignore", "w") as f:
        f.write("node_modules\n.DS_Store\n*.pem\ndist/\n")

    print("\\nDone! \\n1. Run 'npm install'\\n2. Run 'npm run build'\\n3. Open harness/builder.html")

if __name__ == "__main__":
    main()
