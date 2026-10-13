#!/usr/bin/env perl
# Original metadata-only vectors. No camera/OEM data or firmware execution.
# Provider: ExifTool13.59, upstream2200871d, Perl Artistic License or GPL.
use strict;
use warnings;
use Image::ExifTool;
use Digest::SHA qw(sha256_hex);
use JSON::PP;

die "unadmitted ExifTool version\n" unless $Image::ExifTool::VERSION eq '13.59';
my $table = Image::ExifTool::GetTagTable('Image::ExifTool::Olympus::CameraSettings');
open my $source, '<:raw', $INC{'Image/ExifTool/Olympus.pm'} or die "provider unreadable\n";
my $bytes = do { local $/; <$source> };
die "unadmitted Olympus definitions\n" unless sha256_hex($bytes) eq
    'f974dc7c82b5e187148e0defc8d733734445df2121175097f001fe551ae08651';
my $tag = $table->{0x52f};
die "metadata format changed\n" unless $tag->{Count} == 20 && $tag->{Writable} eq 'int16u';
sub decoded_extra {
    my ($code, $slot) = @_;
    my @words = (2,4352,0,0,0,4352,0,0,(0)x12);
    $words[$slot] = $code;
    my $et = Image::ExifTool->new;
    $et->FoundTag($tag, join(' ', @words));
    my @values = split /; /, $et->GetValue('ArtFilterEffect','PrintConv');
    return $values[4];
}
my @result;
for my $case ([0x8040,'Soft Focus'],[0x8080,'Blur Top and Bottom'],[0x8081,'Blur Left and Right']) {
    die "synthetic metadata conversion failed\n" unless decoded_extra($case->[0],4) eq $case->[1];
    push @result, {code=>sprintf('0x%x',$case->[0]), metadata_label=>$case->[1]};
}
die "wrong-slot countercontrol failed\n" unless decoded_extra(0x8040,6) eq 'No Effect';
print JSON::PP->new->canonical->pretty->encode({
    provider=>'ExifTool13.59/2200871d',tag=>'Olympus CameraSettings0x52f',
    count=>20,format=>'int16u',synthetic_cases=>\@result,wrong_slot_control=>'rejected',
    camera_rendering_tested=>JSON::PP::false,oem_input_used=>JSON::PP::false,
});
