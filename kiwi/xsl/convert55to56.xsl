<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv55to56">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv55to56"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.5</literal> to <literal>5.6</literal>.
</para>
<xsl:template match="image" mode="conv55to56">
    <xsl:choose>
        <!-- nothing to do if already at 5.6 -->
        <xsl:when test="@schemaversion > 5.5">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.6">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv55to56"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- transform the pwd attribute of the instrepo element to password -->
<xsl:template match="instsource/instrepo" mode="conv55to56">
    <instrepo>
        <xsl:choose>
            <xsl:when test="@pwd">
                <xsl:attribute name="password">
                    <xsl:value-of select="@pwd"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
        <xsl:copy-of select="@*[not(local-name(.) = 'pwd')]"/>
        <xsl:apply-templates mode="conv55to56"/>
    </instrepo>
</xsl:template>

<!-- transform the pwd attribute of the users element to password -->
<xsl:template match="users/user" mode="conv55to56">
    <user>
        <xsl:choose>
            <xsl:when test="@pwd">
                <xsl:attribute name="password">
                    <xsl:value-of select="@pwd"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
        <xsl:copy-of select="@*[not(local-name(.) = 'pwd')]"/>
        <xsl:apply-templates mode="conv55to56"/>
    </user>
</xsl:template>

<!-- transform the pwd attribute of the repository element to password -->
<xsl:template match="repository" mode="conv55to56">
    <repository>
        <xsl:choose>
            <xsl:when test="@pwd">
                <xsl:attribute name="password">
                    <xsl:value-of select="@pwd"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
        <xsl:copy-of select="@*[not(local-name(.) = 'pwd')]"/>
        <xsl:apply-templates mode="conv55to56"/>
    </repository>
</xsl:template>

</xsl:stylesheet>
