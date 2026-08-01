{
  description = "piepy discord music bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        runtimeLibs = with pkgs; [ libopus libsodium ];
        commonShellHook = ''
            export SSL_CERT_FILE="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath runtimeLibs}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            uv
            ffmpeg
            libopus
            libsodium
            cacert
          ];

          shellHook = commonShellHook;
        };
        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScript "piepy" ''
            ${commonShellHook}
            exec ${pkgs.uv}/bin/uv run piepy "$@"
          ''}";
        };
      }
    );
}
