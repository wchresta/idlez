{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";

  outputs = { self, nixpkgs, flake-utils }:
    {
      nixosModules.default = import ./nixos-module.nix;

      overlays.default = prev: final:
        let
          py = prev.python310Packages;
        in {
          idlez = py.buildPythonPackage {
            pname = "idlez";
            version = "0.0.1";
            src = ./.;

            format = "pyproject";

            nativeBuildInputs = with py; [ setuptools prev.dhall-json ];
            propagatedBuildInputs = with py; [ discordpy ];

            preBuildPhases = [ "buildDhall" ];
            buildDhall = ''
              dhall-to-json --file ./idlez/data/encounters.dhall --output ./idlez/data/encounters.json
              dhall-to-json --file ./idlez/data/elements.dhall --output ./idlez/data/elements.json
            '';

            checkInputs = with py; [ pytest pytestcov mypy ];
            checkPhase = ''
              runHook preCheck
              pytest
              mypy -p idlez
              runHook postCheck
            '';
            doCheck = false;
          };
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlays.default ];
        };
        py = pkgs.python310Packages;

        inherit (pkgs) lib;
      in {
        packages = {
          default = pkgs.idlez;
          idlez = pkgs.idlez;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ pkgs.idlez ];
          buildInputs = with pkgs; [
            black
            py.pytest
            py.pytestcov
            py.mypy
          ];
        };
      });
}
