pkgname=dfuse-iso-writer
pkgver=0.1.0
pkgrel=1
pkgdesc="DFUSE ISO Writer for Linux"
arch=('x86_64')
url="https://github.com/dfuse06/DFUSE-ISO-Writer"
install -Dm644 "$startdir/themes/dfuse_dark.qss" \
"$pkgdir/usr/share/dfuse-iso-writer/themes/dfuse_dark.qss"
license=('MIT')
depends=('glibc' 'polkit')
source=()
sha256sums=()

package() {
    install -Dm755 "$startdir/dist/dfuse-iso-writer" \
        "$pkgdir/usr/bin/dfuse-iso-writer"

    install -Dm644 "$startdir/dfuse_iso.png" \
        "$pkgdir/usr/share/pixmaps/dfuse-iso-writer.png"

    install -Dm644 "$startdir/dfuse-iso-writer.desktop" \
        "$pkgdir/usr/share/applications/dfuse-iso-writer.desktop"

    install -Dm644 "$startdir/LICENSE" \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
