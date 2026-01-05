const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const ModuleFederationPlugin = require('webpack').container.ModuleFederationPlugin;
const DotenvWebpackPlugin = require('dotenv-webpack');

module.exports = {
  mode: process.env.NODE_ENV || 'development',
  entry: './src/main.tsx',
  devtool: 'source-map',
  devServer: {
    port: 3000,
    open: true,
    hot: true,
    historyApiFallback: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.jsx', '.js'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
        },
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/i,
        type: 'asset/resource',
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './index.html',
      inject: true,
    }),
    new DotenvWebpackPlugin({
      systemvars: true,
    }),
    new ModuleFederationPlugin({
      name: 'dashboard',
      filename: 'remoteEntry.js',
      remotes: {
        // You can add remote MFEs here if needed
        // mfe: 'mfe@http://localhost:8027/remoteEntry.js',
      },
      shared: {
        react: {
          singleton: true,
          requiredVersion: '^18.2.0',
          eager: true,
        },
        'react-dom': {
          singleton: true,
          requiredVersion: '^18.2.0',
          eager: true,
        },
        '@auth0/auth0-react': {
          singleton: true,
          requiredVersion: '^2.2.0',
          eager: true,
        },
      },
    }),
  ],
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash].js',
    clean: true,
    publicPath: 'auto',
  },
};

